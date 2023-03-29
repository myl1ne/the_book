from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore_v1 import DocumentReference
import os

import logging
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] - [%(levelname)s] - %(message)s')

class FireStoreDocument:
    __db = None

    def __init__(self, collection, id = None):
        FireStoreDocument.static_init()
        self.__collection = collection
        if id != None:
            self.doc_ref = self.__db.collection(collection).document(id)
        else:
            self.doc_ref = self.__db.collection(collection).document()
    
    @staticmethod
    def static_init():
        if FireStoreDocument.__db == None:
            certificate_path = os.environ.get('THE_BOOK_FIRESTORE_CERTIFICATE_PATH')
            if certificate_path != None:
                initialize_app(credentials.Certificate(certificate_path))
            else:
                initialize_app()
            FireStoreDocument.__db = firestore.client()

    @staticmethod
    def wipe_collection(collection_name):
        def delete_collection(coll_ref, batch_size):
            docs = coll_ref.list_documents(page_size=batch_size)
            deleted = 0

            for doc in docs:
                print(f'Deleting doc {doc.id}')
                doc.delete()
                deleted = deleted + 1

            if deleted >= batch_size:
                return delete_collection(coll_ref, batch_size)
        
        FireStoreDocument.static_init()
        collection_ref = FireStoreDocument.__db.collection(collection_name)
        delete_collection(collection_ref, 10)

    @staticmethod
    def getNewId(colletion_name):
        return FireStoreDocument.__db.collection(colletion_name).document().id

    def id(self):
        return self.doc_ref.id

    def exists(self):
        return self.doc_ref.get().exists

    def get(self):
        return self.doc_ref.get()
    
    def getDict(self):
        dict = document_to_dict(self.get())
        dict['id'] = self.id()
        return dict

    def update(self, value):
        return self.doc_ref.update(value)
    
    def set(self, value):
        return self.doc_ref.set(value)


#Helper methods
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