from pymongo import MongoClient, errors
from typing import List
from utils.conversation import Conversation

class MongoDBManager:
    """Class to manage MongoDB database where Conversation will be saved."""
    
    def __init__(self, uri: str = 'mongodb://localhost:27017/', db_name: str = 'your_database_name', collection_name: str = 'conversations'):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.connect_to_db()
    
    def connect_to_db(self):
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
        except errors.ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
    
    def reconnect_if_needed(self):
        """Check if the connection is closed and reconnect if necessary."""
        if self.client is None or not self.client:
            print("Reconnecting to MongoDB...")
            self.connect_to_db()

    def buscar_conversaciones_por_id(self, conversation_id: str) -> List[dict]:
        """Search conversations by its ID."""
        self.reconnect_if_needed()
        try:
            registros = self.collection.find({'conversation_id': conversation_id})
            return list(registros)
        except errors.InvalidOperation as e:
            print(f"Error occurred while fetching conversations: {e}")
            return []
    
    def add_conversation(self, conversation: Conversation) -> str:
        """Add conversation to the collection."""
        self.reconnect_if_needed()
        try:
            result = self.collection.insert_one(conversation.to_dict())
            return str(result.inserted_id)
        except errors.InvalidOperation as e:
            print(f"Error occurred while adding conversation: {e}")
            return ""
    
    def close_connection(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            print("Connection to MongoDB closed.")