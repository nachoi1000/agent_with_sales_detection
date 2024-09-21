from pymongo import MongoClient
from typing import List
from utils.conversation import Conversation


class MongoDBManager:
    """Class to manage MongoDB database where Conversation will be saved."""
    def __init__(self, uri: str = 'mongodb://localhost:27017/', db_name: str = 'your_database_name', collection_name: str = 'conversations'):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def buscar_conversaciones_por_id(self, conversation_id: str) -> List[dict]:
        """Search conversations by its ID."""
        registros = self.collection.find({'conversation_id': conversation_id})
        return list(registros)
    
    def add_conversation(self, conversation: Conversation) -> str:
        """Add conversation in the colection."""
        result = self.collection.insert_one(conversation.to_dict())
        return str(result.inserted_id)
    
    def close_connection(self):
        """Closes MongoDB conection."""
        self.client.close()