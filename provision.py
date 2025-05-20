import os
from storage.vector_db.vectorstore import ChromaVectorStore
from data_ingestion.indexing.document_handler import process_document
from data_ingestion.indexing.vectorizer import Vectorizer
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the OpenAI API key from the environment variables
api_key = os.environ.get("OPENAI_API_KEY")

persist_directory = os.environ.get("CHROMADB_PERSIST_DIRECTORY")
#persist_directory = "./vectorstore_test"
logging.info(f"persist_directory: {persist_directory}")
data_directory = os.environ.get("DATA_DIRECTORY")
#data_directory = "./data_ingestion/data"
logging.info(f"data_directory: {data_directory}")


# Initialize the Chroma vectorstore with persistence
vectorstore = ChromaVectorStore(
    collection_name=os.environ.get("CHROMADB_COLLECTION_NAME"),
    embedding_function=Vectorizer(api_key).generate_vectors,
    persist_directory=persist_directory
)

# Iterate over the files in the directory
for elemento in os.listdir(data_directory):
    # Construct the full file path
    file_path = os.path.join(data_directory, elemento)
    
    # Process the document
    result = process_document(file_path=file_path, api_key=api_key)

    # Display the result
    print(f"Processing document: {file_path}")
    
    # Add the document to the vectorstore
    vectorstore.add_document(result)

logging.info("Data Ingestion finished!")