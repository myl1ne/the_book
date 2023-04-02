from book.firestore_document import FireStoreDocument
from book.logger import Log
from flask import url_for
   
class User(FireStoreDocument):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'users', id)

    @staticmethod
    def getDefaultsOld():
        return {
            'name': 'John Doe',
            'email': 'john@doe.com',
            'character': {
                'name': 'John Doe',
                'description': 'An average Joe',
                'current_location': 'The Book',
                'image_url': url_for('static', filename='images/default.jpg'),

                'level': 1,
                'experience': 0,
                'next_level': 0,

                'health': 10,
                'maxHealth': 10,

                'strength': 0,
                'agility': 0,
                'intelligence': 0,

                'inventory': [
                    {'name': 'Inked Feather', 'description': 'A feather with ink.', 'image_url': url_for('static', filename='images/item_inked_feather.png')},
                    {'name': 'Empty Scroll', 'description': 'An empty scroll', 'image_url': url_for('static', filename='images/item_scroll.png')},
                ],
                'quests': [
                    {
                        'name': 'The Book', 
                        'description': 'Learn more about The Book and the secrets it contains.', 
                        'status': 'In Progress',
                        'reward': 'Unknown',
                    },
                ],
                'known_locations': ['The Book'],
            }
        }
    
    def getDefaults():
        return {
            'name': 'John Doe',
            'email': 'john@doe.com',
            'character': {
                'inner_daemon_id': FireStoreDocument.getNewId('inner_daemons'),
            }
        }

    def setDefault(self):
        if self.exists():
            Log.error(f'User {self.id()} already exists => Abort')
            return
        self.set(User.getDefaults())
    
    def addKnownLocation(self, location_id):
        if not self.exists():
            Log.error(f'User {self.id()} does not exist => Abort')
            return
        if location_id in self.getDict()['character']['known_locations']:
            Log.error(f'User {self.id()} already knows location {location_id} => Abort')
            return
        self.update({
            'character.known_locations': self.getDict()['character']['known_locations'] + [location_id]
        })