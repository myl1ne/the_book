from book.firestore_document import FireStoreDocument
from book.logger import Log
from book.generator import Generator

class Location(FireStoreDocument):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'locations', id)
    