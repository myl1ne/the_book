from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore_v1 import DocumentReference
import os, re
import openai
import logging
from book.daemon import *
from book.bucket_storage import BucketStorage
from flask import url_for

openai.api_key = os.getenv("OPENAI_API_KEY")
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] - [%(levelname)s] - %(message)s')

def document_to_dict(document):
    def handle_value(value):
        if isinstance(value, DocumentReference):
            return value.id
        elif isinstance(value, dict):
            return {k: handle_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [handle_value(v) for v in value]
        else:
            return value

    data = document.to_dict()
    for key, value in data.items():
        data[key] = handle_value(value)

    return data

def extract_enclosed_string(text):
    pattern = r"<format>(.*?)</format>"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return text
    
class Book:
    def __init__(self):

        #Initialise the Firestore connection
        certificate_path = os.environ.get('THE_BOOK_FIRESTORE_CERTIFICATE_PATH')
        self.cred = credentials.Certificate(certificate_path)
        initialize_app(self.cred)
        self.db = firestore.client()

        #Initialise the GCS connection
        self.bucket_storage = BucketStorage()

        #Configure parameters for visual pipe
        self.visual_generation_config = {
            'requires_safety_checker': False, 
            'height': 512, 'width': 512, 
            'guidance_scale': 7.5,
            'num_inference_steps': 100
        }

    def on_new_user(self, user_id):
        logging.info(f'Creating new user {user_id}')
        doc_ref = self.db.collection('users').document(user_id)

        doc_ref.update({
            'current_location': 'Unknown',
            'character': {
                'name': 'Unknown',
                'description': 'Unknown',
                'image_url': url_for('static', filename='images/default.jpg'),
                'age': 'Unknown',
                'inventory': [],
            },
        })
        user = self.get_character_for_user(user_id)
        logging.info(f'Created new user {user}')
        return user

    def on_new_location(self, loc_id):
        logging.info(f'Creating new location {loc_id}')
        loc_ref = self.db.collection('locations').document(loc_id)
        dae_ref = self.db.collection('daemons').document()

        #create the location and summon a daemon into it
        loc_ref.set({
            'name': loc_id,
            'description': 'Unknown',
            'image_url': url_for('static', filename='images/default.jpg'),
            'paths':[
                {'description':'A door.','destination_id':self.db.collection('locations').document().id}
            ],
            'daemon':dae_ref.id
        })
        #create the daemon
        loc_dict = document_to_dict(loc_ref.get())
        dae_ref.set({
                'name': 'Enoch',
                'bound_location': loc_ref.id,
                'messages': {
                    #contains a list of messages describing what happens to the place
                    'events': 
                    [
                        {"role": "system", "content": get_daemon_base_prompt("Enoch")},
                        {"role": "system", "content": get_daemon_location_prompt(loc_dict)}
                    ],
                    #contains a dictionary indexed by user ID to keep private conversations
                    'chats': {} 
                },
        })
        #Ask the daemon to update the location
        self.update_location(loc_id)
        loc_dict = document_to_dict(loc_ref.get())
        logging.info(f'Created new location {loc_dict}')
        
        #Ask the daemon to update its name
        new_daemon_name = self.ask_large_language_model([{"role": "system", "content": get_daemon_name_from_location(loc_dict)}])
        dae_ref.set({
                'name': new_daemon_name,
                'bound_location': loc_ref.id,
                'messages': {
                    #contains a list of messages describing what happens to the place
                    'events': 
                    [
                        {"role": "system", "content": get_daemon_base_prompt(new_daemon_name)},
                        {"role": "system", "content": get_daemon_location_prompt(loc_dict)}
                    ],
                    #contains a dictionary indexed by user ID to keep private conversations
                    'chats': {} 
                },
        })
        return loc_dict

    def get_character_for_user(self, user_id):
        return document_to_dict(self.db.collection('users').document(user_id).get())['character']
    
    def get_current_location_for(self, user_id):
        logging.info(f'Retrieving current location for user {user_id}')
        user_ref = self.db.collection('users').document(user_id)
        user = document_to_dict(user_ref.get())
        location_ref = self.db.collection('locations').document(user['current_location'])
        location_dict = document_to_dict(location_ref.get())
        response_data = {
            "status": "success",
            "type": "User observing current location",
            "daemon_message": location_dict['description'],
            "image_url": location_dict['image_url']
        }
        return response_data
    
    def move_character_to_location(self, user_id, location_id):
        logging.info(f'Moving user {user_id} to {location_id}')
        user_ref = self.db.collection('users').document(user_id)
        user = document_to_dict(user_ref.get())

        #If the location does not exist, we create it
        location_ref = self.db.collection('locations').document(location_id)
        location = location_ref.get()
        if not location.exists:
            location_dict = self.on_new_location(location_id)
        else:
            location_dict = location.to_dict()
        dae_ref = self.db.collection('daemons').document(location_dict['daemon'])
        dae_ref.update({
            'messages.events': firestore.ArrayUnion([{"role": "system", "content": get_daemon_event_player_arrived(user)}])
        })
        greetings = self.ask_large_language_model(
            dae_ref.get().to_dict()['messages']['events']+
            [{"role": "system", "content":"Greet them with a description of your location."}]
        )
        user_ref.update({
            'current_location': location_ref.id
        })
        logging.info(f'Moving user {user_id} to {location_id} and sent {greetings}')
        response_data = {
            "status": "success",
            "type": "User moved to location",
            "daemon_message": greetings,
            "image_url": location_dict['image_url']
        }
        return response_data

    def process_user_write(self, user_id, text):
        logging.info(f'Process write of {user_id}')
        user = document_to_dict(self.db.collection('users').document(user_id).get())

        location_ref = self.db.collection('locations').document(user['current_location'])
        location_dict = document_to_dict(location_ref.get())

        dae_ref = self.db.collection('daemons').document(location_dict['daemon'])
        #Get the messages with this user if they exist, or the base prompt otherwise
        dae_dict = dae_ref.get().to_dict()
        messages_buff = dae_dict['messages']['chats'].get(user_id,[
                        {"role": "system", "content": get_daemon_base_prompt(dae_dict['name'])},
                        {"role": "system", "content": get_daemon_location_prompt(location_dict)}]
        )
        
        messages_buff.append({"role": "system", "content": get_daemon_event_player_text(user, text)})
        answer = self.ask_large_language_model(messages_buff + [{"role": "system", "content": get_daemon_event_player_text_classification()}])
        logging.info(f'Processed write of {user_id}, answer is {answer}')

        #Update the chat history
        dae_ref.update({
            f'messages.chats.{user_id}': messages_buff + [{"role": "assistant", "content": answer}]
        })
        #execute the action
        answer = extract_enclosed_string(answer)
        move_regex = r".*move_character_to_location\((.+)\).*"
        update_regex = r".*update_location\(\).*"
        answer_regex = r".*answer\((.+)\).*"

        move_match = re.search(move_regex, answer)
        if move_match:
            destination_id = move_match.group(1)
            return self.move_character_to_location(user_id,destination_id)

        update_match = re.search(update_regex, answer)
        if update_match:
            update_json = self.update_location(location_ref.id)
            response_data = {
                "status": "success",
                "type": "User wrote something",
                "daemon_message": update_json['change'],
                "image_url": update_json['updated_location']['image_url']
            }
            return response_data

        answer_match = re.search(answer_regex, answer)
        if answer_match:
            answer = answer_match.group(1)
            response_data = {
                "status": "success",
                "type": "User wrote something",
                "daemon_message": answer,
                "image_url": location_dict['image_url']
            }
            return response_data
        
        response_data = {
                "status": "success",
                "type": "User wrote something",
                "daemon_message": f"The daemon speaks in tongues, maybe you can understand: {answer}",
                "image_url": location_dict['image_url']
        }
        return response_data
    
    def update_location(self, location_id):
        logging.info(f'Updating location {location_id}')
        location_ref = self.db.collection('locations').document(location_id)
        location_doc = location_ref.get()
        if not location_doc.exists:
            logging.error(f'Trying to update a non-existing location with id {location_id}')
            pass

        location_dict = document_to_dict(location_doc)
        dae_ref = self.db.collection('daemons').document(location_dict['daemon'])
        dae_doc = dae_ref.get()
        msgs = dae_doc.to_dict()['messages']['events']
        msgs.append({"role": "system", "content": get_daemon_event_location_update(location_dict)})
        update_msg = self.ask_large_language_model(msgs)
        enclosed_msg = extract_enclosed_string(update_msg)
        update_json = json.loads(enclosed_msg)
        logging.info(f'Updating location {location_id} with changes {update_msg}')
        
        #Generate the new image URL
        update_json['updated_location']['image_url'] = self.generate2D(update_json['updated_location']['description'])

        #Update the location doc
        location_ref.update(update_json['updated_location'])
        
        #Add to the daemon history
        dae_ref.update({
            'messages.events':firestore.ArrayUnion([{"role": "system", "content": f"You updated the location with: '{update_json['change']}'"}])
        })
        logging.info(f'Updated location {location_id}')
        return update_json
    
    def ask_large_language_model(self, messages):
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        logging.info("chatgpt response: " + str(chat_completion))
        return chat_completion.choices[0].message.content
    
    def generate2D(self, prompt: str) -> str:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size=str(self.visual_generation_config["height"]) + "x" + str(self.visual_generation_config["width"]),
        )
        image_url = response['data'][0]['url']

        return self.bucket_storage.fetch_and_host_image(image_url)