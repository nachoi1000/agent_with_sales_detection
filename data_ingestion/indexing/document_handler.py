from typing import List, Optional
from chunker import Chunker
from loader import LocalLoader
from vectorizer import Vectorizer
from documents import Document


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
        chunker = Chunker(chunk_size=1000, chunk_overlap_size=200)
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