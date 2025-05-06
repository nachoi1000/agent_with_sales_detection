from typing import Callable, List
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from deep_translator import GoogleTranslator
from langdetect import detect
from collections import defaultdict
import numpy as np
from sentence_transformers import CrossEncoder
import nltk
nltk.download('stopwords')
nltk.download('punkt_tab')


class RetrievalStrategies:

    cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    @staticmethod
    def text_search(query_texts: List[str], collection, n_results: int) -> List[str]:
        """
        Text-based search strategy with lexical analysis.
        Steps: lower-casing, stop word removal, and stemming.
        """
        # Initialize the stop words set stemmer and the tanslator
        stop_words = set(stopwords.words('english'))
        stemmer = PorterStemmer()
        translator = GoogleTranslator(source='auto', target='en')

        def preprocess(text: str) -> List[str]:
            """Lowercase, remove stop words, and apply stemming."""
            #if it text is not in english, translate it
            if detect(text) != 'en':
                text = translator.translate(text)
            # Tokenize the text
            tokens = word_tokenize(text.lower())
            # Remove non-alphanumeric characters and stop words, then apply stemming
            filtered_tokens = [
                stemmer.stem(token) for token in tokens if token.isalnum() and token not in stop_words
            ]
            return filtered_tokens

        # Preprocess the query texts
        processed_queries = [preprocess(query) for query in query_texts]

        # Retrieve all documents from the collection
        all_elements = collection.query_texts(
            query_texts=processed_queries,
            n_results=50,
            include=["documents", "metadatas"]
        )
        ##all_elements = collection.get(include=["documents", "metadatas"])
        
        # Score documents based on the number of matching terms with the processed queries
        document_scores = defaultdict(int)
        for query_terms in processed_queries:
            for idx, (doc, metadata) in enumerate(zip(all_elements["documents"], all_elements["metadatas"])):
                # Preprocess the document content
                processed_doc = preprocess(doc)
                # Calculate the number of matching terms
                matches = sum(1 for term in query_terms if term in processed_doc)
                # Accumulate the score for the document
                document_scores[idx] += matches
        
        # Sort documents by score in descending order
        ranked_documents = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)

        # Retrieve the top N results based on scores
        top_documents = [
            {
            "document": all_elements["documents"][idx],
            "id": all_elements["ids"][idx],
            "metadata": all_elements["metadatas"][idx]
            }
            for idx, _ in ranked_documents[:n_results]
            ]
    
        return {
            "documents": [doc["document"] for doc in top_documents],
            "ids": [doc["id"] for doc in top_documents],
            "metadatas": [doc["metadata"] for doc in top_documents]
        }

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
        results = collection.query(query_embeddings=query_embeddings, n_results=n_results)
        return results

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

        # Check if n_results is even, if it's not, make it even by adding 1
        if n_results % 2 > 0:
            n_results += 1

        text_results = RetrievalStrategies.text_search(query_texts, collection, int(n_results/2))
        vector_results = RetrievalStrategies.vector_search(query_texts, embedding_function, collection, int(n_results/2))
        
        # Combine the results by merging the lists from both search results
        combined_results = {
            "documents": text_results["documents"] + vector_results["documents"],
            "ids": text_results["ids"] + vector_results["ids"],
            "metadatas": text_results["metadatas"] + vector_results["metadatas"]
        }

        return combined_results

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
        initial_results = RetrievalStrategies.vector_search(query_texts, embedding_function, collection, n_results * 2)
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
    

    def retrieve(self, strategy_name: str, query_texts: list, n_results: int = 5):
        if not hasattr(self, strategy_name):
            raise ValueError(f"Strategy {strategy_name} is not defined.")
        strategy = getattr(self, strategy_name)
        return strategy(query_texts=query_texts, n_results=n_results)