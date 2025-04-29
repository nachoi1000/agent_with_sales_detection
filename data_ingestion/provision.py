import os
import sys

# Get the parent directory (assuming `data_ingestion` is a subdirectory)
sys.path.append(os.path.join(os.path.dirname(__file__), 'indexing'))

from indexing.vectorstore import ChromaVectorStore
from indexing.document_handler import process_document
from indexing.vectorizer import Vectorizer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the OpenAI API key from the environment variables
api_key = os.environ.get("THE_OPENAI_API_KEY")

# Get the current working directory
current_directory = os.getcwd()

# Set the full path for the "vectorstore" folder
persist_directory = os.path.join(current_directory, "vectorstore")

# Initialize the Chroma vectorstore with persistence
vectorstore = ChromaVectorStore(
    collection_name="rag_collection",
    embedding_function=Vectorizer(api_key).generate_vectors,
    persist_directory=persist_directory
)

# Get the directory containing the files from environment variables
data_directory = os.environ.get("DATA_DIRECTORY")

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
