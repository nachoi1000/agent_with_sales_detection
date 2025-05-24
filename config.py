import os
import logging
from utils.file_manager import FileManager
from storage.db.db_manager import MongoDBManager
from storage.vector_db.vectorstore import ChromaVectorStore
from utils.llm_manager import Assistant, RAG
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

limit_messages_in_conversation = int(os.environ.get("LIMIT_MESSAGES_IN_CONVERSATION"))
threshold_sales_intention_trigger = int(os.environ.get("THRESHOLD_SALES_INTENTION_TRIGGER"))
privacy_policy_uri = os.environ.get("PRIVACY_POLICY_URI")

#Mongo
db_manager_conversations = MongoDBManager(collection_name="conversations", uri = f'mongodb://localhost:27017/')
db_manager_userdata = MongoDBManager(collection_name="userdata", uri = f'mongodb://localhost:27017/')

#ChormaDB Vectorstore
collection_name = os.environ.get("CHROMADB_COLLECTION_NAME")
logging.debug(f"collection_name: {collection_name}")
persist_directory = os.environ.get("CHROMADB_PERSIST_DIRECTORY")
logging.debug(f"persist_directory: {persist_directory}")
vectorstore = ChromaVectorStore(collection_name=collection_name, persist_directory=persist_directory)


# RAG and Assistants
file_manager = FileManager()
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
assistant_model = "gpt-4o-mini"
detector_model = "o3-mini"
rag_model = "gpt-4o"

valid_retrieval_strategies = {"text_search", "vector_search", "hybrid_search", "reranking"}
retrieval_strategy = os.environ.get("RAG_RETRIEVAL_STRATEGY")
if retrieval_strategy not in valid_retrieval_strategies:
    raise ValueError(
        f"Invalid retrieval strategy '{retrieval_strategy}'. "
        f"Must be one of: {', '.join(valid_retrieval_strategies)}"
    )

#Assistant Content FIlter
content_filter_prompt = file_manager.load_md_file("prompts/content_filter.md")
assistant_content_filter = Assistant(client=client, base_prompt=content_filter_prompt, model=assistant_model)

#Assistant Conversation Memory  
conversation_memory_prompt = file_manager.load_md_file('prompts/conversation_memory.md')
assistant_memory = Assistant(client=client, base_prompt=conversation_memory_prompt, model=assistant_model)

#Assistant Sales Detector  
sales_detector_prompt = file_manager.load_md_file('prompts/sales_detector.md')
assistant_sales_detector = Assistant(client=client, base_prompt=sales_detector_prompt, model=detector_model)

#Assistant Consentiment   
consentiment_prompt = file_manager.load_md_file('prompts/consentiment.md')
assistant_consentiment = Assistant(client=client, base_prompt=consentiment_prompt, model=detector_model)

#Assistant Request Data  
request_data_prompt = file_manager.load_md_file("prompts/request_user_data.md")
assistant_request_data = Assistant(client=client, base_prompt=request_data_prompt, model=assistant_model)

#RAG
rag_prompt = file_manager.load_md_file('prompts/quantum_rag.md')
rag = RAG(client=client, base_prompt=rag_prompt, vectorstore=vectorstore, retrieval_strategy=retrieval_strategy)
