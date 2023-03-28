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
        user.setDefault()
        return user.getDict()

    def create_new_location(self, loc_id):
        Log.info(f'Creating new location {loc_id}')
        loc = Location(loc_id)

        #create the location and summon a daemon into it
        loc.setDefault()
        loc_dict = loc.getDict()
        #create the daemon
        dae = Daemon(loc_dict['daemon'])
        dae.setDefault(name = 'Enoch', loc_id = loc.id())

        #Ask the daemon to update the location
        dae.update_location("You and this place are now bound together. Make it your own.")

        loc_dict = loc.getDict()
        Log.info(f'Created new location {loc_dict}')
        
        #Ask the daemon to update its name
        if loc_id != "The Book":
            new_daemon_name = dae.ask_large_language_model([{"role": "system", "content": Daemon.get_daemon_name_from_location(loc_dict)}])
            dae.set(Daemon.getDefaults(new_daemon_name, loc.id()))
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
            location_dict = self.create_new_location(location_id)
        else:
            location_dict = location.getDict()

        user.update({
            'current_location': location.id()
        })
        user.addKnownLocation(location.id())
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

        if answer['classification'] == 'adventurer_took_exit_path':
            return self.move_character_to_location(user_id,answer['destination_id'])
        
        if answer['classification'] == 'adventurer_took_action_leading_to_narrative':   
            response_data = {
                "status": "success",
                "type": "User wrote something",
                "daemon_message": answer['daemon_answer'],
                "image_url": location_dict['image_url']
            }
            return response_data
        
        if answer['classification'] == 'adventurer_took_action_leading_to_dialog':   
            response_data = {
                "status": "success",
                "type": "User wrote something",
                "daemon_message": answer['daemon_answer'],
                "image_url": location_dict['image_url']
            }
            return response_data
        
        if answer['classification'] == 'adventurer_took_action_leading_to_location_update':   
            response_data = {
                "status": "success",
                "type": "User wrote something",
                "daemon_message": answer['update_json']['change'],
                "image_url": answer['update_json']['updated_location']['image_url']
            }
            return response_data        

        if answer['classification'] == 'adventurer_took_action_leading_inventory_update':   
            response_data = {
                "status": "success",
                "type": "User wrote something",
                "daemon_message": answer['update_json']['change'],
                "image_url": location_dict['image_url']
            }
            return response_data        

        return {
                "status": "success",
                "type": "User wrote something",
                "daemon_message": f"The daemon speaks in tongues, maybe you can understand: {answer['daemon_answer']}",
                "image_url": location_dict['image_url']
        }
    
