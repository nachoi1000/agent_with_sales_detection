import os
from typing import Callable, List, Dict, Optional
import chromadb
from documents import Document
#from retriever import RetrievalStrategies

class ChromaVectorStore:
    def __init__(self, collection_name: str, embedding_function: Callable, persist_directory: Optional[str] = None, metric: str = "cosine"):
        """
        Initializes the ChromaDB vectorstore client and sets up a collection.
        :param collection_name: The name of the collection for your vectors.
        :param persist_directory: Directory to store persistent data (optional, if persistence is required).
        """
        
        # if persist_directory is not None, make sure that it exists
        if persist_directory:
            # Make directory if it does not exists
            os.makedirs(persist_directory, exist_ok=True)
            # Init client with persists
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            # Init client without persists
            self.client = chromadb.Client()
            
        self.collection_name = collection_name
        self.metric = metric  
        self.collection = self.get_or_create_collection()
        self.embedding_function = embedding_function

    def get_or_create_collection(self):
        """
        Retrieves an existing collection or creates a new one.
        :return: The ChromaDB collection object.
        """
        return self.client.get_or_create_collection(
        name=self.collection_name,
        metadata={"hnsw:space": self.metric})

    def add_document(self, document: Document):
        """
        Adds a single document's chunks along with their vector embeddings and optional metadata.
        :param document: Document object containing chunks and vectors.
        """
        if document.chunks and document.vectors:
            if document.vectors is None or not all(isinstance(v, list) for v in document.vectors):
                raise ValueError("Invalid vectors; ensure embeddings are generated.")
            # Generate metadata for each chunk
            metadatas = [{"file_path": document.file_path, "file_name": document.file_name} for _ in document.chunks]
            # Add chunks with pre-computed vectors and metadata (like file path or file name)
            self.collection.add(
                documents=document.chunks,
                ids=[f"{document.file_name}_chunk_{i}" for i in range(len(document.chunks))],
                embeddings=document.vectors,
                metadatas=metadatas # Metadata for each chunk
            )

    def OLD_query(self, query_texts: List[str], n_results: int = 5):
        """
        Queries the vectorstore for the closest documents to the provided query texts.
        :param query_texts: List of query text to find similar documents.
        :param n_results: Number of results to return.
        :return: List of matched document IDs and their metadata.
        """
        # Generar embeddings para los textos de consulta usando la misma función
        query_embeddings = [self.embedding_function(query)[0] for query in query_texts]

        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )
        return results
    
    #def query(self, query_texts: List[str], n_results: int = 5, strategy: Callable = RetrievalStrategies.default_strategy):
    #    """
    #    Queries the vectorstore for the closest documents to the provided query texts.
    #    :param query_texts: List of query texts to find similar documents.
    #    :param n_results: Number of results to return.
    #    :param strategy: Strategy to use for retrieval (default: default strategy).
    #    :return: List of matched document IDs and their metadata.
    #    """
    #    # Use the strategy for querying the vector store
    #    return strategy(query_texts, self.embedding_function, self.collection, n_results)

    def delete_documents(self, ids: List[str]):
        """
        Deletes documents by their IDs.
        :param ids: List of document IDs to be deleted.
        """
        self.collection.delete(ids=ids)

    def get_metadata(self, ids: List[str]):
        """
        Retrieves metadata for specific document IDs.
        :param ids: List of document IDs to retrieve metadata for.
        :return: Metadata for the documents.
        """
        return self.collection.get(ids=ids, include=["metadatas"])

    def get_all_elements(self):
        """
        Retrieve all elements in the collection (documents, embeddings, metadata).
        """
        results = self.collection.get(include=["metadatas", "documents", "embeddings"])
        return results
    



