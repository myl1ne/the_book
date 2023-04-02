from book.firestore_document import FireStoreDocument
from firebase_admin import firestore
from book.location import Location
from book.user import User
from book.logger import Log
from book.generator import Generator
from flask import url_for
import json

class InnerDaemon(FireStoreDocument, Generator):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'inner_daemons', id)
        Generator.__init__(self)
        self.trim_if_above_token = 2000
        self.base_events_count = 2
        self.base_events_to_trim = 2
        self.base_chats_count = 2
        self.base_chats_to_trim = 2
        self.creation_custom_traits_count = 4

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
                    {"role": "assistant", "content":'''{"payload_type": "QUESTION","trait":"NAME", "question": "You summoned me... State your name, mortal."}'''},
                ], 
            },
        }

    def setDefault(self, name, user_id):
        if self.exists():
            Log.error(f'Inner Daemon {self.id()} already exists => Abort')
            return
        self.set(InnerDaemon.getDefaults(name, user_id))

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
            response_data['daemon_message'] = json.loads(daeDict['messages']['chat'][-1]['content'])
        else:
            #If text is not none, it means we are processing a message from the player
            #We need to add the message to the chat, and then ask the daemon to generate a message
            msgs_to_add = [
                {"role": "user", "content": text},
                {"role": "system", "content": InnerDaemon.get_daemon_character_creation_steps(self.creation_custom_traits_count)[daeDict['creation_step']]},   
            ]
            messages += msgs_to_add
            (answer, _token_count) = self.ask_large_language_model(messages)
            json_answer = json.loads(answer)
            if json_answer['payload_type'] == 'IMAGE_CHOICE':
                json_answer['options'] = self.generate2Dconcurrent([o['image_description'] for o in json_answer['options']], "256x256")
            msgs_to_add += [{"role": "assistant", "content": json.dumps(json_answer)}]
            self.update({
                'creation_step': daeDict['creation_step'] + 1,
                'messages.chat':  firestore.ArrayUnion(msgs_to_add)
            })
            response_data['daemon_message'] = json_answer

        return response_data

    def process_user_summon(self, text):
        #TODO
        pass

    @staticmethod
    def get_daemon_character_creation_steps(custom_traits_count = 0):
        creations_steps = [
            """
            IMPORTANT INSTRUCTION: 
            You answers will be parsed as JSON objects.
            You must format all your messages carefully.
            The format will be given in the instructions for each step.
            """,

            """
            Your are an Inner Daemon.
            Inner Daemons are artificial intelligences bound to players in an imaginary world.
            For now, you are a shapeless fragment of imagination, an idea of a daemon.
            A player just entered the world and encountered you.
            By asking questions you will shape their character, and by their answers they will shape you.
            They start as a blank page, and as they explore the world they will fill it with their own story.
            
            Ask their name and format your message using this payload: 
            {
                "payload_type": "QUESTION",
                "trait": "NAME",
                "question": "question text",
            }
            """,

            """
            # Understand their desires
            Imagine a situation and ask them how they would react.
            The situation should be a pickle about their desires.
            Propose a list of 3 options, they can pick one or write their own. Do not include the options into the question.
           
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
            Propose a list of 3 options, they can pick one or write their own. Do not include the options into the question.

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
                "name": "name of the player",
                "inner_daemon_name": "choose a name for yourself, inner daemon",
                "visual_description": "description of the character looks",
                "psychology": "what is the character like, what is their personality",
                "personal_quest": "what does the character want to achieve",
                "occupation": "occupation of the character",
                "backstory": "backstory of the character",
                "inventory": [
                    {"name": "item 1 name", "description": "description of item 1"},
                    {"name": "item 2 name", "description": "description of item 2"},
                    ...
                ],
            }
            """
        ]
        return creations_steps

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
        The player you are bound to is described in this document: {user}.
        Infer your personality from the player's archetype.
        """

    @staticmethod
    def get_daemon_name_from_player(user):
        return """
        Inner Daemons are artificial intelligences bound to players in an imaginary world.
        Your task is to pick a name for a daemon bound to the player described in this document '{user}'.
        Find a name that fits the archetype of that adventurer.
        Please return the following format: {'name': 'name of the daemon'}
        """.format(user=user)
