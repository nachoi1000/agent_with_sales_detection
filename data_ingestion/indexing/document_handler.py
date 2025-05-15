import os
from typing import List, Optional
from data_ingestion.indexing.chunker import Chunker
from data_ingestion.indexing.loader import LocalLoader
from data_ingestion.indexing.vectorizer import Vectorizer
from data_ingestion.indexing.documents import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
chunk_size = int(os.environ.get("CHUNKER_CHUNK_SIZE"))
chunk_overlap = int(os.environ.get("CHUNKER_CHUNK_OVERLAP"))


def process_document(file_path: str, api_key: str) -> Optional[Document]:
    """
    Main function to process a document by loading it, chunking its content, and generating vectors.
    
    Args:
        file_path (str): The path to the document file to be processed.
        api_key (str): The OpenAI API key for generating vectors.
    
    Returns:
        Document: The processed document with chunks and vectors, or None if an error occurs.
    """
    try:
        # Step 1: Load the document and generate its content
        document = Document(file_path=file_path)
        loader = LocalLoader(document=document)
        document.content = loader.load()
        
        # Step 2: Chunk the document content
        chunker = Chunker(chunk_size=chunk_size, chunk_overlap_size=chunk_overlap)
        chunks = chunker.generate_chunks([document.content])
        document.add_chunks(chunks)
        
        # Step 3: Generate vectors for the chunks using OpenAI embeddings
        vectorizer = Vectorizer(api_key)
        vectors = vectorizer.generate_vectors(document.chunks)
        document.add_vectors(vectors)
        
        return document

    except Exception as e:
        print(f"An error occurred while processing the document: {e}")
        return None  # Optionally handle it differently (e.g., logging)