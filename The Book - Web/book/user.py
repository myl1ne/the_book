from book.firestore_document import FireStoreDocument
from book.logger import Log

class User(FireStoreDocument):
    def __init__(self, id = None):
        FireStoreDocument.__init__(self, 'users', id)
