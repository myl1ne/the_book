from book.firestore_document import FireStoreDocument
from book.logger import Log
from book.generator import Generator
from flask import url_for

class Location(FireStoreDocument):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'locations', id)
    
    @staticmethod
    def getDefaults(loc_id):
        return {
            'name': loc_id,
            'description': 'Unknown',
            'image_url': url_for('static', filename='images/default.jpg'),
            'paths':[
                {'description':'A door.','destination_id':FireStoreDocument.getNewId('locations')}
            ],
            'daemon':FireStoreDocument.getNewId('daemons')
        }

    def setDefault(self):
        if self.exists():
            Log.error(f'Location {self.id()} already exists => Abort')
            return
        self.set(Location.getDefaults(self.id()))