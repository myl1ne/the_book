from book.firestore_document import FireStoreDocument
from firebase_admin import firestore
from book.location import Location
from book.logger import Log
from book.generator import Generator
import json
import re

class Daemon(FireStoreDocument, Generator):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'daemons', id)
        Generator.__init__(self)
        self.trim_if_above_token = 2000
        self.base_events_count = 2
        self.base_events_to_trim = 2
        self.base_chats_count = 2
        self.base_chats_to_trim = 2

    @staticmethod
    def getDefaults(name, loc_id):
        loc = Location(loc_id)
        return {
            'name': name,
            'bound_location': loc.id(),
            'messages': {
                #contains a list of messages describing what happens to the place
                'events': 
                [
                    {"role": "system", "content": Daemon.get_daemon_base_prompt(name)},
                    {"role": "system", "content": Daemon.get_daemon_location_prompt(loc.getDict())}
                ],
                #contains a dictionary indexed by user ID to keep private conversations
                'chats': {} 
            },
        }

    def setDefault(self, name, loc_id):
        if self.exists():
            Log.error(f'Daemon {self.id()} already exists => Abort')
            return
        self.set(Daemon.getDefaults(name, loc_id))

    #TODO move the trim logic inside the register methods and make them a transaction
    def register_events(self, events):
        self.update({
            'messages.events': firestore.ArrayUnion(events)
        })

    #TODO move the trim logic inside the register methods and make them a transaction
    def register_summons(self, user_id, summons_messages):
        self.update({
            f'messages.chats.{user_id}': firestore.ArrayUnion(summons_messages)
        })

    def greet_user(self, user)->str:
        dae_dict = self.getDict()
        location = Location(dae_dict['bound_location'])
        location_dict = location.getDict()
        messages = [
            {"role": "system", "content": Daemon.get_daemon_base_prompt(dae_dict['name'])},
            {"role": "system", "content": Daemon.get_daemon_location_prompt(location_dict)},
            {"role": "system", "content": Daemon.get_daemon_event_player_arrived(user['character'])},
            {"role": "system", "content":"Greet them with a description of your location."}
        ]
        (greetings, _token_count) = self.ask_large_language_model(messages)
        return greetings                

    def update_location(self, reason_for_updating):
        dae_dict = self.getDict()
        location = Location(dae_dict['bound_location'])
        location_dict = location.getDict()

        events = dae_dict['messages']['events']
        events += [{"role": "system", "content": Daemon.get_daemon_event_location_update(location_dict, reason_for_updating)}]

        trials = 0
        max_trials = 3
        success = False
        while (not success and trials < max_trials):
            try:
                (update_msg, token_count) = self.ask_large_language_model(events)
                enclosed_msg = extract_enclosed_string(update_msg)
                update_json = json.loads(enclosed_msg)
                success = True
            except:
                Log.error(f'Failed to parse update message: {enclosed_msg}. Retrying...')
                trials += 1
        if (not success):
            Log.error(f'Failed to parse update message {max_trials} times')
            raise Exception(f'Failed to parse update message: {enclosed_msg}')
        
        Log.info(f'Updating location {location.id()} with changes {update_msg}')
        
        #Generate the new image URL
        update_json['updated_location']['image_url'] = self.generate2D(update_json['updated_location']['description'])

        #Update the location doc
        location.update(update_json['updated_location'])
        
        #Add to the daemon history & trim if needed
        evt = {"role": "system", "content": f"You updated the location with: '{update_json['change']}'"}
        if (token_count > self.trim_if_above_token):
            del events[self.base_events_count:self.base_events_count+self.base_events_to_trim]
            self.update({
                'messages.events':events+[evt]
            })
        else:
            self.register_events([evt])

        return update_json

    def process_user_summon(self, user_dict, text):
        dae_dict = self.getDict()

        #TODO optimize, the location is fetched twice
        location = Location(dae_dict['bound_location'])
        location_dict = location.getDict()

        #If we have not history with the user, we register the base prompts
        if user_dict['id'] not in dae_dict['messages']['chats']:
            self.register_summons(user_dict['id'], 
                    [
                        {"role": "system", "content": Daemon.get_daemon_base_prompt(dae_dict['name'])},
                        {"role": "system", "content": Daemon.get_daemon_location_prompt(location_dict)}
                    ]
            )            
        #Register the new message from the user
        self.register_summons(user_dict['id'],[{"role": "system", "content": Daemon.get_daemon_event_player_text(user_dict, text)}])
        #refresh the dict
        dae_dict = self.getDict()

        #Buffer with the classifcation prompt
        message_classes = [
            ('adventurer_took_action_leading_away', '(pick this if the adventurer left the current location or entered one of the paths.)'), 
            ('adventurer_took_action_leading_to_narrative', '(pick this if the action led to a narrative event)'), 
            ('adventurer_took_action_leading_to_dialog', '(pick this if the action led to a verbal answer from the daemon)'),
            ('adventurer_took_action_leading_to_location_update', '(pick this if the action affected the state of the location)'),
        ]
        chats = dae_dict['messages']['chats'][user_dict['id']]
        messages_buff = chats + [{"role": "system", "content": Daemon.get_daemon_event_player_text_classification(classes=message_classes)}]
        (answer, token_count) = self.ask_large_language_model(messages_buff)

        #execute the action
        answer_data = {
                "classification": "failure",
                "daemon_answer": answer,
        }
        evt = [{"role": "system", "content": "You processed the message as: " + json.dumps(answer_data)}]
        if 'adventurer_took_action_leading_away' in answer:
            messages_buff = chats + [{"role": "system", "content": Daemon.get_daemon_event_player_text_get_destination()}]
            (destination_id, token_count) = self.ask_large_language_model(messages_buff)
            answer_data = {
                "classification": "adventurer_took_action_leading_away",
                "destination_id": destination_id,
            }
            evt = [{"role": "assistant", "content": "I send you to " + destination_id}]

        if 'adventurer_took_action_leading_to_narrative' in answer:            
            messages_buff = chats + [{"role": "system", "content": Daemon.get_daemon_event_player_text_answer_with_narrative()}]
            (answer, token_count) = self.ask_large_language_model(messages_buff)
            answer_data = {
                "classification": "adventurer_took_action_leading_to_narrative",
                "daemon_answer": answer,
            }
            evt = [{"role": "assistant", "content": answer}]

        if 'adventurer_took_action_leading_to_dialog' in answer:            
            messages_buff = chats + [{"role": "system", "content": Daemon.get_daemon_event_player_text_answer_with_dialog()}]
            (answer, token_count) = self.ask_large_language_model(messages_buff)
            answer_data = {
                "classification": "adventurer_took_action_leading_to_dialog",
                "daemon_answer": answer,
            }
            evt = [{"role": "assistant", "content": answer}]

        if 'adventurer_took_action_leading_to_location_update' in answer:            
            answer_data = {
                "classification": "adventurer_took_action_leading_to_location_update",
                "update_json": self.update_location(reason_for_updating="Adventurer wrote:'{text}'"),
            }
            evt = [{"role": "assistant", "content": answer_data['update_json']['change']}]

        #Register the answer / clean up the history
        if (token_count > self.trim_if_above_token):
            del chats[self.base_chats_count:self.base_chats_count+self.base_chats_to_trim]
            self.update({f'messages.chat.{user_dict["id"]}': chats+evt})
        else:
            self.register_summons(user_dict['id'],evt)
        Log.info(f'Processed write of {user_dict["id"]} ==> {answer}')

        return answer_data
    
    @staticmethod
    def get_daemon_base_prompt(name):
        return f"""
        You are {name}.
        You are a daemon bound to a location in an imaginary world.
        In this world, players can move between locations and interact through text with each other and with you.
        Your duty is to give life to world by reacting to players actions.
        You are both a game master, a storyteller and a character in the world.
        Roleplay your character: DO NOT SAY you are an AI, instead say you are a daemon, a ghost, a spirit or something else of your choosing.
        You define your own personality and you can be helpful, but you don't have to.
        """

    @staticmethod
    def get_daemon_location_prompt(location):
        return f"""
        The location you are bound to is described in this document: {location}.
        Infer your personality from the location: for example if the location is a forest, you could be a peaceful tree spirit. If it is a volcano, you could be a fiesty fire demon, etc.
        """

    @staticmethod
    def get_daemon_name_from_location(location):
        return f"""
        Daemons are artificial intelligences bound to locations in an imaginary world.
        Your task is to pick a name for a daemon bound to the location described in this document '{location}'.
        Find a name that fits the description of the location.
        Please return a string that is the name of the daemon (return ONLY THE NAME, without any other text).
        """

    @staticmethod
    def get_daemon_event_player_arrived(character):
        return f"""
        An adventurer just arrived to your location. They are described by this document: {character}.
        """

    @staticmethod
    def get_daemon_event_player_text(character, text):
        return f"""
        You have received a text written by the following adventurer '{character}'
        Here is the written text: '{text}'.
        """

    @staticmethod
    def get_daemon_event_player_text_classification(classes):
        classes_str = '\n'.join([f'{item[0]} {item[1]}' for item in classes])

        return f"""
        Your task is to classify the text you just received.
        Return one of the following strings (ONLY RETURN THE CLASS STRING, without any other text or explanation):
            {classes_str}
        """

    @staticmethod
    def get_daemon_event_player_text_get_destination():
        return f"""
        Please return a string that is the id of the destination location (return ONLY THE ID, don't write any other text or explanation).
        """
    
    @staticmethod
    def get_daemon_event_player_text_answer_with_narrative():
        return f"""
        Please return a string that is the narrative you want to send to the player.
        Be descriptive and use the third person for all characters, including yourself and the player.
        Don't write any spoken dialog.
        Wrap the string in <narrative> and </narrative> tags.
        """

    @staticmethod
    def get_daemon_event_player_text_answer_with_dialog():
        return f"""
        Please return a string that is the speech you want to send to the player.
        Wrap the string in <dialog> and </dialog> tags.
        """
    
    @staticmethod
    def get_daemon_event_location_update(location, reason_for_updating):
        format = json.dumps({
            'change':'A narrative description of what changed and how. It may be sent to present players.',
            'updated_location': location
        })
        return f"""
        As the daemon of your location, it is up to you to make it evolve.
        You must update the location document because {reason_for_updating}.
        Here is its current document: {location}.
        Please return a document with any adjustments you'd like to make.
        Remember a few rules:
        - DO NOT MODIFY THE KEYS OF THE JSON STRUCTURE, only the values
        - your main task is to update the description
        - you can add or remove paths, but there should always be at least 1
        - the destination_id of a path should be less than 3 words, ideally 1
        
        <format>{format}</format>

        IMPORTANT: your answer will be parsed by a regex: follow scrupulously the format within the tags. Do not send the tags.
        """

def extract_enclosed_string(text):
    pattern = r"<format>(.*?)</format>"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return text