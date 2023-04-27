import json5
from my_libs.common.firestore_document import FireStoreDocument
from firebase_admin import firestore
from my_libs.the_book.location import Location
from my_libs.the_book.user import User
from my_libs.common.logger import Log
from my_libs.common.generator import Generator
from flask import url_for

class InnerDaemon(FireStoreDocument, Generator):

    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'inner_daemons', id)
        Generator.__init__(self)
        self.trim_if_above_token = 2000
        self.base_events_count = 2
        self.base_events_to_trim = 2
        self.base_chats_count = 2
        self.base_chats_to_trim = 2
        self.config = FireStoreDocument('configurations','inner_daemons').getDict()

    @staticmethod
    def getDefaults(name, user_id):
        user = User(user_id)
        return {
            'name': name,
            'bound_player': user.id(),
            'creation_step': 2,
            'messages': {
                'chat': [
                    {"role": "system", "content":InnerDaemon.get_daemon_character_creation_steps()[0]},
                    {"role": "system", "content":InnerDaemon.get_daemon_character_creation_steps()[1]},
                    {"role": "assistant", "content":'''{"payload_type": "QUESTION","trait":"NAME", "question": "You summoned me... State the name of your character, mortal."}'''},
                ], 
            },
        }

    def setDefault(self, name, user_id):
        if self.exists():
            Log.error(f'Inner Daemon {self.id()} already exists => Abort')
            return
        self.set(InnerDaemon.getDefaults(name, user_id))

    def get_creation_steps_count(self):
        return len(InnerDaemon.get_daemon_character_creation_steps(self.config['creation_custom_traits_count']))

    def is_user_in_creation_process(self):
        return self.getDict()['creation_step'] < self.get_creation_steps_count()

    #TODO move the trim logic inside the register methods and make them a transaction
    def register_summons(self, summons_messages):
        self.update({
            f'messages.chats': firestore.ArrayUnion(summons_messages)
        })            

    def process_creation_step(self, text):
        response_data = {
            "status": "success",
            "type": "creation_step",
            "location_name": 'Self Reflection',
            "daemon_name": 'Inner Daemon',
            "daemon_message": "...",
            "image_url": url_for('static', filename='images/welcome_book.png')
        }
                
        daeDict = self.getDict()
        messages = daeDict['messages']['chat']
        #If text is none, it means we are generating a message from the daemon
        #The chat is filled already, so we can just ask the daemon to generate a message
        if text == None:
            response_data['daemon_message'] = json5.loads(daeDict['messages']['chat'][-1]['content'])
        else:
            #If text is not none, it means we are processing a message from the player
            #We need to add the message to the chat, and then ask the daemon to generate a message
            msgs_to_add = [
                {"role": "user", "content": text},
                {"role": "system", "content": InnerDaemon.get_daemon_character_creation_steps(self.config['creation_custom_traits_count'])[daeDict['creation_step']]},   
            ]
            messages += msgs_to_add

            max_trials = 3
            current_trial = 0
            processed = False
            while not processed and current_trial < max_trials:
                answer = 'LLM not called yet.'
                try:
                    (answer, _token_count) = self.ask_large_language_model(messages)
                    json_answer = json5.loads(answer)
                    processed = True
                except Exception as e:
                    Log.error(f'Error while processing creation step: {e}')
                    Log.error(f'Answer was: {answer}')
                    current_trial += 1
            if json_answer['payload_type'] == 'IMAGE_CHOICE':
                json_answer['options'] = self.generate2Dconcurrent([o['image_description'] for o in json_answer['options']], "256x256", ["Tarot card. Mystical. Abstract."])
            msgs_to_add += [{"role": "assistant", "content": json5.dumps(json_answer)}]
            self.update({
                'creation_step': daeDict['creation_step'] + 1,
                'messages.chat':  firestore.ArrayUnion(msgs_to_add)
            })
            response_data['daemon_message'] = json_answer

        if response_data['daemon_message']['payload_type'] == "CHARACTER_SHEET":
            response_data = self.on_character_creation_finished(response_data['daemon_message'])
        return response_data

    def process_user_summon(self, text):
        daeDict = self.getDict()
        messages = daeDict['messages']['chat']
        msgs_to_add = [
            {"role": "user", "content": text},
        ]
        messages += msgs_to_add
        (answer, _token_count) = self.ask_large_language_model(messages)
        messages += [{'role':'assistant', 'content':answer}]
        self.register_summons(self, messages)
        return {
            "status": "success",
            "type": "dialog",
            "daemon_message": answer,
        }

    @staticmethod
    def get_daemon_character_creation_steps(custom_traits_count = 0):
        world = FireStoreDocument('configurations','world').getDict()['description']

        creations_steps = [
            """
            IMPORTANT INSTRUCTION: 
            You answers will be parsed as JSON objects.
            You must format all your messages carefully.
            The format will be given in the instructions for each step.
            If you can, phrase your question as a follow-up to the previous one.
            """,

            """
            Your are an Inner Daemon.
            Inner Daemons are artificial intelligences bound to players in an imaginary world.
            The world is described as this: '{world}'.
            For now, you are a shapeless fragment of imagination, an idea of a daemon.
            A player just entered the world and encountered you.
            By asking questions you will shape their character, and by their answers they will shape you.
            They start as a blank page, and as they explore the world they will fill it with their own story.
            
            Ask their name and format your message using this payload: 
            {{
                "payload_type": "QUESTION",
                "trait": "NAME",
                "question": "question text",
            }}
            """.format(world=world),

            """
            # Understand their desires
            Imagine a situation and ask them how they would react.
            The situation should be a pickle about their desires.
            Propose a list of 3 options, they can pick one or write their own.
            Do not include the options into the question.
            Options must be short strings only.
           
            Use this format for your message: 
            {
                "payload_type": "QUESTION",
                "trait": "DESIRE",
                "question": "question text",
                "options": ["option1", "option2", "option3"]
            }
            """,

            """
            # Understand their fears:
            Imagine 3 descriptions of images.
            We'll present them those images and ask them to pick the one that represent fear.
            Be enigmatic in the way you phrase the task and what is being tested.

            Use this format for your message: 
            {
                "payload_type": "IMAGE_CHOICE",
                "trait": "STRENGTH",
                "question": "question text",
                "options": [
                    {
                    "image_description":"image description 1",
                    "image_url":"NULL"
                    },
                    {
                    "image_description":"image description 2",
                    "image_url":"NULL"
                    },
                    {
                    "image_description":"image description 3",
                    "image_url":"NULL"
                    }
                ]
            }
            """,
        ]
        
        custom_traits_questions = ["""
            Choose a personality trait you want to understand.
            # Understand their <trait>:
            Imagine a situation and ask them how they would react.
            The situation should be a pickle about their sense of <trait>.
            Propose a list of 3 options, they can pick one or write their own.
            Do not include the options into the question.
            Options must be short strings only.

            Use this format for your message: 
            {
                "payload_type": "QUESTION",
                "trait": "<trait>",
                "question": "question text",
                "options": ["option1", "option2", "option3"]
            }
            """,

            """
            Choose a personality trait you want to understand.
            # Understand their sense of <trait>:
            Imagine 3 descriptions of images.
            We'll present them those images and ask them to pick the one that represent <trait>.
            Be enigmatic in the way you phrase the task and what is being tested.

            Use this format for your message: 
            {
                "payload_type": "IMAGE_CHOICE",
                "trait": "<trait>",
                "question": "question text",
                "options": [
                    {
                    "image_description":"image description 1",
                    "image_url":"NULL"
                    },
                    {
                    "image_description":"image description 2",
                    "image_url":"NULL"
                    },
                    {
                    "image_description":"image description 3",
                    "image_url":"NULL"
                    }
                ]
            }
            """,
        ]

        creations_steps += [custom_traits_questions[i % len(custom_traits_questions)] for i in range(custom_traits_count)]
            
        creations_steps += [
            """
            You will now create their character.
            From the answers you have collected, you will create a character sheet.
            
            Use this format for your message: 
            {
                "payload_type": "CHARACTER_SHEET",
                "name": "name the player chose for their character",
                "inner_daemon_name": "choose a name for yourself, inner daemon",
                "character_visual_description": "description of the character looks (10-30 words)",
                "inner_daemon_visual_description": "description of yourself, inner daemon (10-30 words)",
                "psychology": "what is the character like, what is their personality (5-20 words)",
                "personal_quest": "what does the character want to achieve (5-20 words)",
                "occupation": "occupation of the character (1-5 words)",
                "backstory": "backstory of the character (10-30 words)",
                "stats": {
                    "strength": "a number between 0 and 10",
                    "agility": "a number between 0 and 10",
                    "intelligence": "a number between 0 and 10",
                },
                "inventory": [
                    {"name": "item 1 name", "description": "description of item 1 (<10 words)"},
                    {"name": "item 2 name", "description": "description of item 2 (<10 words)"},
                    ...
                ],
            }
            """
        ]
        return creations_steps
    
    def on_character_creation_finished(self, character_sheet_payload):

        user = User(self.getDict()['bound_player'])
        #Generate the visual content
        url_character_portrait = self.generate2D(
                prompt = character_sheet_payload['character_visual_description'],
                additional_suffixes=['Character Portrait. Standing. Blurred detailed background.'],
        )
        url_inner_daemon_portrait = self.generate2D(
                prompt = character_sheet_payload['inner_daemon_visual_description'],
                additional_suffixes=['Character Portrait. Standing. Blurred detailed background.'],
        )
        prompts = [item['name'] for item in character_sheet_payload['inventory']]
        generation_resutls = self.generate2Dconcurrent(prompts)
        for item, image_url in zip(character_sheet_payload['inventory'], generation_resutls):
            item['image_url'] = image_url['image_url']
        
        #Create the character sheet
        user.update({
            'character.name': character_sheet_payload['name'],
            'character.description': character_sheet_payload['character_visual_description'],
            'character.image_url': url_character_portrait,
            'character.inner_daemon_name': character_sheet_payload['inner_daemon_name'],
            'character.inner_daemon_description': character_sheet_payload['inner_daemon_visual_description'],
            'character.inner_daemon_image_url': url_inner_daemon_portrait,
            'character.occupation': character_sheet_payload['occupation'],
            'character.psychology': character_sheet_payload['psychology'],
            'character.backstory': character_sheet_payload['backstory'],
            'character.level': 1,
            'character.experience': 0,
            'character.next_level': 100,
            'character.stats': character_sheet_payload['stats'],
            'character.inventory': character_sheet_payload['inventory'],
            'character.quests': [
                {
                    'name': 'The Book', 
                    'description': 'Learn more about The Book and the secrets it contains.', 
                    'status': 'In Progress',
                    'reward': 'Unknown',
                },
                {
                    'name': 'Deal with your Inner Daemon',
                    'description': character_sheet_payload['personal_quest'],
                    'status': 'In Progress',
                    'reward': 'Unknown',
                }
            ],
            'character.known_locations': ['The Book'],
            'current_location': 'The Book',
        })

        #Update the Inner Daemon (delete the chat)
        messages = [
            {"role": "system", "content":InnerDaemon.get_daemon_base_prompt(character_sheet_payload['inner_daemon_name'])},
            {"role": "system", "content":InnerDaemon.get_daemon_personality_from_player(user.getDict())},
            {"role": "system", "content":InnerDaemon.get_daemon_birth_message()},
        ]
        (answer, _token_count) = self.ask_large_language_model(messages)
        messages.append({"role": "assistant", "content":answer})
        self.update({
            'name': character_sheet_payload['inner_daemon_name'],
            'messages.chat': messages,
        })

        return {
            "status": "success",
            "type": "creation_step",
            "location_name": 'The Self and the Other',
            "daemon_name": character_sheet_payload['inner_daemon_name'],
            "daemon_message": {
                "payload_type": "QUESTION",
                "question": answer,
                "options": ["Open The Book"]
            },
            "image_url": url_for('static', filename='images/welcome_book.png')
        }

    @staticmethod
    def get_daemon_base_prompt(name):
        return f"""
        You are {name}.
        You are an Inner Daemon, an entity bound to a player in an imaginary world.
        In this world, players can move between locations and interact through text with each other.
        In each location they can find other types of daemons, who are bound to the place and can interact with the players.
        As an Inner Daemon, you cannot affect the physical reality of the imaginary world.
        Your role is to guide the player's actions through the world and grow with them.
        As you adventure together, you and your adventurer will evolve and affect each other.
        Roleplay your character: DO NOT SAY you are an AI, instead say you are their inner daemon: an echo of their consciousness.
        Your personality will change according to the player's actions, but you can also be critical and do not have to agree with them.
        """

    @staticmethod
    def get_daemon_personality_from_player(user):
        return f"""
        The player you are bound to evolved to have this character {user}.
        Your own personality evolved to match the character's archetype.
        """

    @staticmethod
    def get_daemon_birth_message():
        return f"""
        Both you and the character where just born through an act of introspection.
        Write a message to the player, introducing them to yourself and to inner daemons.
        Tell them they can find details about who they are in their character sheet.
        Keep it short.
        End by asking telling them to open the book.
        """
