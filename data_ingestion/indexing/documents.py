from typing import List


class Document:
    def __init__(self, file_path: str, content: str = "", chunks: List[str] = None, vectors: List[List[float]] = None):
        """
        Initialize a Document object to store the content, file path, chunks, and vectors.
        
        Args:
            content (str): The raw content of the document.
            file_path (str): The path to the document file.
            chunks (List[str]): List of text chunks from the document.
            vectors (List[List[float]]): List of vectors generated for each chunk.
        """
        self.content = content
        self.file_path = file_path
        self.file_name = self.extract_file_name(file_path)
        self.chunks = chunks if chunks is not None else []
        self.vectors = vectors if vectors is not None else []

    def __repr__(self):
        return f"Document(file_name={self.file_name!r}, file_path={self.file_path!r}, content={self.content[:100]!r}...)"

    def extract_file_name(self, file_path: str) -> str:
        """Extract the file name from the file path."""
        return file_path.split('/')[-1]  # Modify as needed for your OS

    def add_chunks(self, chunks: List[str]):
        """
        Add chunks to the document.
        
        Args:
            chunks (List[str]): List of text chunks.
        """
        self.chunks.extend(chunks)  # Append to existing chunks

    def add_vectors(self, vectors: List[List[float]]):
        """
        Add vectors to the document.
        
        Args:
            vectors (List[List[float]]): List of vectors for the text chunks.
        """
        self.vectors.extend(vectors)  # Append to existing vectors