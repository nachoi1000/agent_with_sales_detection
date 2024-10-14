from typing import Callable, List
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from googletrans import Translator
from langdetect import detect
from collections import defaultdict
import re


# text_search
# vector_search
# hybrid_search
# HyDE
# reranking
# this strategy: https://cookbook.openai.com/examples/question_answering_using_a_search_api
# https://medium.com/@tridib.tcg/a-guide-to-azure-ai-search-retrieval-methods-5a4b0673b817#:~:text=Performing%20Searches,search%20and%20hybrid%20%2B%20semantic%20ranking.

# THE query_texts IT AHS TO BE A LIST OF 1 DIMENSION LEN(query_texts) == 1!!!!
class RetrievalStrategies:

    @staticmethod
    def text_search(query_texts: List[str], embedding_function: Callable, collection, n_results: int) -> List[str]:
        """
        Text-based search strategy with lexical analysis.
        Steps: lower-casing, stop word removal, and stemming.
        """
        # Initialize the stop words set stemmer and the tanslator
        stop_words = set(stopwords.words('english'))
        stemmer = PorterStemmer()
        translator = Translator()

        def preprocess(text: str) -> List[str]:
            """Lowercase, remove stop words, and apply stemming."""
            #if it text is not in english, translate it
            if detect(text) != 'en':
                text = translator.translate(text, dest='en').text
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
        all_elements = collection.get(include=["documents", "metadatas"])
        
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

        text_results = RetrievalStrategies.text_search(query_texts, embedding_function, collection, n_results/2)
        vector_results = RetrievalStrategies.vector_search(query_texts, embedding_function, collection, n_results/2)
        
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

        hyde_prompt = "hyde_prompt"
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
        rerank_prompt = "rerank_prompt"
        rerank_texts = [f"Generated context for: {query}" for query in query_texts]
        # Step 1: Initial retrieval using vector search
        initial_results = RetrievalStrategies.vector_search(query_texts, embedding_function, collection, n_results * 2)
        
        # Step 2: Re-rank the results using a secondary metric, e.g., some custom scoring
        reranked_results = RetrievalStrategies._rerank_results(initial_results, query_texts, n_results)
        return reranked_results

    @staticmethod
    def _merge_results(text_results, vector_results, n_results):
        """
        Helper function to merge text and vector search results.
        """
        # Placeholder logic: combine and truncate results to `n_results`
        merged = text_results + vector_results
        return merged[:n_results]

    @staticmethod
    def _rerank_results(initial_results, query_texts, n_results):
        """
        Helper function to re-rank results.
        """
        # Placeholder logic: sort by some custom score and truncate to `n_results`
        reranked = sorted(initial_results, key=lambda x: x['score'], reverse=True)
        return reranked[:n_results]