import os
from typing import Callable, List, Dict, Optional
import chromadb
from data_ingestion.indexing.documents import Document
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv
from retriever import RetrievalStrategies

# Load environment variables
load_dotenv()
# Get the OpenAI API key from the environment variables
api_key = os.environ.get("OPENAI_API_KEY")

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name="text-embedding-ada-002"
            )


class ChromaVectorStore:
    def __init__(self, collection_name: str, embedding_function: Optional[Callable] = openai_ef, persist_directory: Optional[str] = None, metric: str = "cosine"):
        """
        Initializes the ChromaDB vectorstore client and sets up a collection.
        :param collection_name: The name of the collection for your vectors.
        :param persist_directory: Directory to store persistent data (optional, if persistence is required).
        :param embedding_function: The embedding function to use. Defaults to OpenAI embedding function.
        :param metric: The distance metric to use for the collection.
        """
        
        # if persist_directory is not None, make sure that it exists
        if persist_directory:
            # Make directory if it does not exist
            os.makedirs(persist_directory, exist_ok=True)
            # Init client with persistence
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            # Init client without persistence
            self.client = chromadb.Client()

        self.collection_name = collection_name
        self.metric = metric  
        self.collection = self.get_or_create_collection()

        # If no embedding function is provided, use OpenAI's embedding function
        if embedding_function is None:
            pass
            #self.embedding_function = OpenAIEmbeddingFunction(api_key=api_key, model_name="text-embedding-ada-002")
        else:
            self.embedding_function = embedding_function

        self.retrieval_strategies = RetrievalStrategies()

    def get_or_create_collection(self):
        """
        Retrieves an existing collection or creates a new one.
        :return: The ChromaDB collection object.
        """
        return self.client.get_or_create_collection(
        name=self.collection_name,
        metadata={"hnsw:space": self.metric},
        embedding_function= openai_ef)

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

    def query_embeddings(self, query_texts: List[str], n_results: int = 5):
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
    
    def query_texts(self, query_texts: List[str], n_results: int = 5):
        """
        Queries the vectorstore for the closest documents to the provided query texts.
        :param query_texts: List of query text to find similar documents.
        :param n_results: Number of results to return.
        :return: List of matched document IDs and their metadata.
        """

        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )
        return results

    def get_content_from_results(self, results: dict) -> str:
        """
        Retrieves the content of documents from the results and concatenates them into a single string.
        :param results: Dictionary containing the results with 'documents' as a key.
        :return: Concatenated string with the content of each document.
        """
        # Retrieve the list of lists of documents and concatenate each element
        content = "\n\n".join(doc for sublist in results.get("documents", []) for doc in sublist)
        return content
    
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

    def apply_retrieval_strategy(self, strategy_name: str, query_texts: List[str], n_results: int = 5):
        """
        Applies a retrieval strategy by its name.
        :param strategy_name: The name of the retrieval strategy to apply.
        :param query_texts: List of query texts.
        :param n_results: Number of results to return.
        :return: Results of the retrieval strategy.
        """
        if not hasattr(self.retrieval_strategies, strategy_name):
            raise ValueError(f"Strategy {strategy_name} is not defined in RetrievalStrategies.")
        
        strategy = getattr(self.retrieval_strategies, strategy_name)
        return strategy(query_texts=query_texts, embedding_function=self.embedding_function, collection=self.collection, n_results=n_results)



