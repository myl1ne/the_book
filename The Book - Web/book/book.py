import re
from book.logger import Log
from book.user import User
from book.location import Location
from book.daemon import Daemon, extract_enclosed_string
from flask import url_for
   
class Book:
    def __init__(self):
        pass

    def on_new_user(self, user_id):
        Log.info(f'Creating new user {user_id}')
        user = User(user_id)
        user.update({
            'current_location': 'Unknown',
            'character': {
                'name': 'Unknown',
                'description': 'Unknown',
                'image_url': url_for('static', filename='images/default.jpg'),
                'age': 'Unknown',
                'inventory': [],
            },
        })
        return user.getDict()

    def on_new_location(self, loc_id):
        Log.info(f'Creating new location {loc_id}')
        loc = Location(loc_id)
        dae = Daemon()

        #create the location and summon a daemon into it
        loc.set({
            'name': loc_id,
            'description': 'Unknown',
            'image_url': url_for('static', filename='images/default.jpg'),
            'paths':[
                {'description':'A door.','destination_id':Location.getNewId('locations')}
            ],
            'daemon':dae.id()
        })
        #create the daemon
        dae.set({
                'name': 'Enoch',
                'bound_location': loc.id(),
                'messages': {
                    #contains a list of messages describing what happens to the place
                    'events': 
                    [
                        {"role": "system", "content": Daemon.get_daemon_base_prompt("Enoch")},
                        {"role": "system", "content": Daemon.get_daemon_location_prompt(loc.getDict())}
                    ],
                    #contains a dictionary indexed by user ID to keep private conversations
                    'chats': {} 
                },
        })
        #Ask the daemon to update the location
        self.update_location(loc_id)
        loc_dict = loc.getDict()
        Log.info(f'Created new location {loc_dict}')
        
        #Ask the daemon to update its name
        if loc_id != "The Book":
            new_daemon_name = dae.ask_large_language_model([{"role": "system", "content": Daemon.get_daemon_name_from_location(loc_dict)}])
            dae.set({
                    'name': new_daemon_name,
                    'bound_location': loc.id(),
                    'messages': {
                        #contains a list of messages describing what happens to the place
                        'events': 
                        [
                            {"role": "system", "content": Daemon.get_daemon_base_prompt(new_daemon_name)},
                            {"role": "system", "content": Daemon.get_daemon_location_prompt(loc_dict)}
                        ],
                        #contains a dictionary indexed by user ID to keep private conversations
                        'chats': {} 
                    },
            })
        return loc_dict

    def get_current_location_for(self, user_id):
        Log.info(f'Retrieving current location for user {user_id}')
        user = User(user_id)
        user_dict = user.getDict()
        location = Location(user_dict['current_location'])
        location_dict = location.getDict()
        response_data = {
            "status": "success",
            "type": "User observing current location",
            "daemon_message": location_dict['description'],
            "image_url": location_dict['image_url']
        }
        return response_data
    
    def move_character_to_location(self, user_id, location_id):
        user = User(user_id)        

        location = Location(location_id)
        if not location.exists():
            location_dict = self.on_new_location(location_id)
        else:
            location_dict = location.getDict()

        user.update({
            'current_location': location.id()
        })
        user_dict = user.getDict()

        dae = Daemon(location_dict['daemon'])
        dae.register_events([{"role": "system", "content": Daemon.get_daemon_event_player_arrived(user_dict)}])
        greetings = dae.greet_user(user_dict)

        Log.info(f'Moving user {user_id} to {location_id} ==> {greetings}')
        response_data = {
            "status": "success",
            "type": "User moved to location",
            "daemon_message": greetings,
            "image_url": location_dict['image_url']
        }
        return response_data

    def process_user_write(self, user_id, text):
        Log.info(f'Process write of {user_id}')
        user = User(user_id)
        user_dict = user.getDict()

        location = Location(user_dict['current_location'])
        location_dict = location.getDict()

        dae = Daemon(location_dict['daemon'])
        answer = dae.process_user_summon(user_dict, text)

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
            update_json = self.update_location(location.id())
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
        Log.info(f'Updating location {location_id}')
        location = Location(location_id)
        if not location.exists():
            Log.error(f'Trying to update a non-existing location with id {location_id}')
            pass
        location_dict = location.getDict()
        dae = Daemon(location_dict['daemon'])
        update_json = dae.update_location()
        Log.info(f'Updated location {location_id}')
        return update_json
    
