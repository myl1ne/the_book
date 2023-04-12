from my_libs.common.firestore_document import FireStoreDocument
from my_libs.common.logger import Log
from my_libs.common.generator import Generator
from flask import url_for

class Location(FireStoreDocument):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'locations', id)
    
    @staticmethod
    def getDefaults(loc_id):
        return {
            'name': loc_id,
            'description': '<a description of the place (less than 30 words)>',
            'image_url': url_for('static', filename='images/default.jpg'),
            'exit_paths':[
                {
                    'description':'<a description of what the exit looks like (less than 10 words)>',
                    'destination_id':'<the name of the place this exit leads to (1-3 words)>'
                }
            ],
            'NPCs':[
                {
                    'name':'<the name of a non playable character', 
                    'description':'<description of the character. (less than 10 words)>',
                }
            ],
            'pickable_objects':[
                {
                    'name':'<the name of an object', 
                    'description':'<description of the object. (less than 10 words)>'
                }
            ],
            'daemon':FireStoreDocument.getNewId('daemons')
        }

    def setDefault(self):
        if self.exists():
            Log.error(f'Location {self.id()} already exists => Abort')
            return
        self.set(Location.getDefaults(self.id()))