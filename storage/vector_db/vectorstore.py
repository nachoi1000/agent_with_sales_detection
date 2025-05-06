import inspect
import os
from typing import Callable, List, Dict, Optional
import chromadb
from data_ingestion.indexing.documents import Document
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi

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
    #def apply_retrieval_strategy(self, strategy_name: str, query_texts: List[str], n_results: int = 5):
        if not hasattr(self.retrieval_strategies, strategy_name):
            raise ValueError(f"Strategy {strategy_name} is not defined in RetrievalStrategies.")
        
        strategy = getattr(self.retrieval_strategies, strategy_name)
        
        # Recolectar todos los argumentos posibles
        available_args = {
            "query_texts": query_texts,
            "embedding_function": self.embedding_function,
            "collection": self.collection,
            "n_results": n_results
        }

        # Inspeccionar la firma de la función y filtrar solo los argumentos que acepta
        sig = inspect.signature(strategy)
        valid_args = {
            k: v for k, v in available_args.items() if k in sig.parameters
        }

        return strategy(**valid_args)


class RetrievalStrategies:

    cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    @staticmethod
    def text_search(query_texts: List[str], embedding_function: Callable, collection, n_results: int): #BM25
        """
        Hybrid BM25 strategy: retrieves a subset of documents using vector search,
        then applies BM25 scoring over them.
        
        :param query_texts: List of query texts.
        :param embedding_function: Embedding function (used for initial filtering).
        :param collection: The ChromaDB collection to search.
        :param n_results: Number of results to return.
        :return: List of BM25-scored top results.
        """
        from rank_bm25 import BM25Okapi
        import numpy as np

        query = query_texts[0]

        # Paso 1: Recuperar los documentos candidatos (ej. top 50) usando búsqueda vectorial
        initial_results = collection.query(
            query_texts=[query],
            n_results=max(n_results * 3, 30),
            include=["documents", "metadatas"]  # "ids" no es válido aquí
        )
        
        ids = initial_results["ids"][0]
        documents = initial_results["documents"][0]
        metadatas = initial_results["metadatas"][0]

        # Paso 2: Aplicar BM25 sobre los documentos recuperados
        tokenized_corpus = [doc.lower().split() for doc in documents]
        tokenized_query = query.lower().split()

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:n_results]

        return [
            {
                "id": ids[i],
                "document": documents[i],
                "metadata": metadatas[i],
                "score": float(scores[i])
            }
            for i in top_indices
        ]

    @staticmethod
    def vector_search(query_texts: List[str], embedding_function: Callable, collection, n_results: int):
        """
        Searches for documents by vector similarity.
        :param query_texts: List of query texts to find similar documents.
        :param embedding_function: Function to convert text into vector embeddings.
        :param collection: The ChromaDB collection to search.
        :param n_results: Number of results to return.
        :return: List of matched document IDs and their metadata.
        """
        query_embeddings = [embedding_function(query)[0] for query in query_texts]
        initial_results = collection.query(query_embeddings=query_embeddings, n_results=n_results)
        
        ids = initial_results["ids"][0]
        documents = initial_results["documents"][0]
        metadatas = initial_results["metadatas"][0]
        
        return [
            {
                "id": doc_id,
                "document": doc,
                "metadata": meta
            }
            for doc, meta, doc_id in zip(documents, metadatas, ids)
        ]

    @staticmethod
    def hybrid_search(query_texts: List[str], embedding_function: Callable, collection, n_results: int):
        """
        Combines text search and vector search.
        :param query_texts: List of query texts to find similar documents.
        :param embedding_function: Function to convert text into vector embeddings.
        :param collection: The ChromaDB collection to search.
        :param n_results: Number of results to return.
        :return: Combined list of results from text and vector searches.
        """
        if n_results % 2 > 0:
            n_results += 1

        half = n_results // 2
        text_results = RetrievalStrategies.text_search(query_texts, embedding_function, collection, half)
        vector_results = RetrievalStrategies.vector_search(query_texts, embedding_function, collection, half)

        combined_results = text_results + vector_results

        # Quitar duplicados si es necesario por ID
        seen_ids = set()
        unique_results = []
        for r in combined_results:
            if r["id"] not in seen_ids:
                unique_results.append(r)
                seen_ids.add(r["id"])

        unique_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return unique_results[:n_results]

    @staticmethod
    def HyDE(query_texts: List[str], embedding_function: Callable, collection, n_results: int):
        """
        Hypothetical Document Embeddings (HyDE) strategy.
        :param query_texts: List of query texts.
        :param embedding_function: Function to generate synthetic embeddings for query texts.
        :param collection: The ChromaDB collection to search.
        :param n_results: Number of results to return.
        :return: List of results from HyDE search.
        """

        #file_manager = FileManager()
        #hyde_prompt = file_manager.load_md_file(file_path="hyde_prompt.md")
        hyde_prompt = "test"
        hyde_texts = [f"Generated context for: {query}" for query in query_texts]
        results = RetrievalStrategies.vector_search(hyde_texts, embedding_function, collection, n_results)
        return results

    @staticmethod
    def reranking(query_texts: List[str], embedding_function: Callable, collection, n_results: int):
        """
        Re-ranking strategy: initial vector search followed by re-ranking.
        :param query_texts: List of query texts.
        :param embedding_function: Function to convert text into vector embeddings.
        :param collection: The ChromaDB collection to search.
        :param n_results: Number of results to return.
        :return: List of re-ranked results.
        """
        query_embeddings = [embedding_function(query)[0] for query in query_texts]
        initial_results = collection.query(query_embeddings=query_embeddings, n_results=n_results* 2)
        reranked_results = RetrievalStrategies._rerank_results(initial_results, query_texts, n_results)
        return reranked_results

    @staticmethod
    def _rerank_results(initial_results, query_texts, n_results):
        """
        Re-ranks initial results based on similarity scores computed by a cross-encoder model.
        :param initial_results: Initial retrieval results with document contents.
        :param query_texts: List of query texts.
        :param n_results: Number of results to return.
        :return: List of top re-ranked results.
        """

        # Ensure we are working with a single query text (for simplicity)
        query = query_texts[0]

        # Extraer los documentos del primer query
        retrieved_documents = initial_results["documents"][0]
        retrieved_ids = initial_results["ids"][0]
        retrieved_metadatas = initial_results["metadatas"][0]

        # Prepare pairs of (query, document) for cross-encoder scoring
        pairs = [[query, doc] for doc in retrieved_documents]

        # Get similarity scores from the cross-encoder
        scores = RetrievalStrategies.cross_encoder.predict(pairs)

        # Sort indices based on scores in descending order
        sorted_indices = np.argsort(scores)[::-1]

        # Construir los resultados re-rankeados como lista de dicts
        reranked_results = [
            {
                "id": retrieved_ids[i],
                "document": retrieved_documents[i],
                "metadata": retrieved_metadatas[i],
                "score": float(scores[i])
            }
            for i in sorted_indices[:n_results]
        ]

        return reranked_results

