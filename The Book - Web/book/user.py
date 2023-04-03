from book.firestore_document import FireStoreDocument
from book.logger import Log
from flask import url_for
   
class User(FireStoreDocument):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'users', id)

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
    
    def getLiteCharacterDict(self):
        if not self.exists():
            Log.error(f'User {self.id()} does not exist => Abort')
            return
        user = self.getDict()
        return {
            'id': user['id'],
            'current_location': user['current_location'],
            'character': {
                'name': user['character']['name'],
                'description': user['character']['description'],
                'level': user['character']['level'],
                'stats': user['character']['stats'],
                'inventory': user['character']['inventory'],
                'inner_daemon_id': user['character']['inner_daemon_id'],
                'known_locations': user['character']['known_locations'],
            }
        }