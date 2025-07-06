# database.py
# This file is used to manage database connections and operations.


from pymongo import MongoClient
from settings import MONGO_URI 


def get_client():
    client = MongoClient(MONGO_URI)
    return client

def get_database():
    def _get_database():
        client = get_client()
        db = client.get_default_database()
        return db
    return _get_database