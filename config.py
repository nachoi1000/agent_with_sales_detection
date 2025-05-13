import os
from utils.file_manager import FileManager
from storage.db.db_manager import MongoDBManager
from storage.vector_db.vectorstore import ChromaVectorStore
from utils.llm_manager import Assistant, RAG
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

limit_messages_in_conversation = int(os.environ.get("LIMIT_MESSAGES_IN_CONVERSATION"))

#Mongo
mongo_initdb_root_username = os.environ.get("MONGO_INITDB_ROOT_USERNAME")
mongo_initdb_root_password = os.environ.get("MONGO_INITDB_ROOT_PASSWORD")
#db_manager_conversations = MongoDBManager(collection_name="conversations", uri = f'mongodb://{mongo_initdb_root_username}:{mongo_initdb_root_password}@localhost:27017/')
#db_manager_userdata = MongoDBManager(collection_name="userdata", uri = f'mongodb://{mongo_initdb_root_username}:{mongo_initdb_root_password}@localhost:27017/')
db_manager_conversations = MongoDBManager(collection_name="conversations", uri = f'mongodb://localhost:27017/')
db_manager_userdata = MongoDBManager(collection_name="userdata", uri = f'mongodb://localhost:27017/')

#ChormaDB Vectorstore
collection_name = os.environ.get("CHROMADB_COLLECTION_NAME")
persist_directory = os.environ.get("CHROMADB_PERSIST_DIRECTORY")
vectorstore = ChromaVectorStore(collection_name=collection_name, persist_directory=persist_directory)


# RAG and Assistants
file_manager = FileManager()
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

#Assistant Content FIlter
content_filter_prompt = file_manager.load_md_file("prompts/content_filter.md")
assistant_content_filter = Assistant(client=client, base_prompt=content_filter_prompt)

#Assistant Conversation Memory  
conversation_memory_prompt = file_manager.load_md_file('prompts/conversation_memory.md')
assistant_memory = Assistant(client=client, base_prompt=conversation_memory_prompt)

#Assistant Sales Detector  
sales_detector_prompt = file_manager.load_md_file('prompts/sales_detector.md')
assistant_sales_detector = Assistant(client=client, base_prompt=sales_detector_prompt)

#Assistant Consentiment   
consentiment_prompt = file_manager.load_md_file('prompts/consentiment.md')
assistant_consentiment = Assistant(client=client, base_prompt=consentiment_prompt)

#Assistant Request Data  
request_data_prompt = file_manager.load_md_file("prompts/request_user_data.md")
assistant_request_data = Assistant(client=client, base_prompt=request_data_prompt)

#RAG
rag_prompt = file_manager.load_md_file('prompts/quantum_rag.md')
rag = RAG(client=client, base_prompt=rag_prompt, vectorstore=vectorstore, retrieval_strategy=os.environ.get("RAG_RETRIEVAL_STRATEGY"))
