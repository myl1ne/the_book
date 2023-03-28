from book.firestore_document import FireStoreDocument
from book.logger import Log
from flask import url_for
   
class User(FireStoreDocument):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'users', id)

    @staticmethod
    def getDefaults():
        return {
            'name': 'John Doe',
            'email': 'john@doe.com',
            'character': {
                'name': 'Unknown',
                'description': 'Unknown',
                'current_location': 'Unknown',
                'image_url': url_for('static', filename='images/default.jpg'),
                'level': 1,
                'inventory': [],
                'quests': [],
                'known_locations': [],
            }
        }

    def setDefault(self):
        if self.exists():
            Log.error(f'User {self.id()} already exists => Abort')
            return
        self.set(User.getDefaults())