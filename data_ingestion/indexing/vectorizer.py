from openai import OpenAI
from typing import List
client = OpenAI()

class Vectorizer:
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        """
        Initialize the Vectorizer with OpenAI API credentials and the embedding model.
        
        Args:
            api_key (str): The OpenAI API key.
            model (str): The embedding model to use (default is "text-embedding-ada-002").
        """
        client.api_key = api_key
        self.model = model

    def generate_vectors(self, chunks: List[str]) -> List[List[float]]:
        """
        Generates embeddings (vectors) for the provided list of chunks using the OpenAI API.

        Args:
            chunks (List[str]): A list of text chunks to generate embeddings for.

        Returns:
            List[List[float]]: A list of embedding vectors corresponding to the input chunks.
        """
        vectors = []
        for chunk in chunks:
            response = client.embeddings.create(input=chunk, model=self.model)
            vector = response.data[0].embedding
            vectors.append(vector)
        return vectors