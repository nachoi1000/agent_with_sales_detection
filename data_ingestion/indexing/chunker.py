import re
from typing import List

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap_size: int = 200):
        """
        Initialize the Chunker with chunk size and chunk overlap size.
        
        Args:
            chunk_size (int): The maximum size of each chunk. Default is 1000.
            chunk_overlap_size (int): The number of overlapping characters between chunks. Default is 200.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap_size = chunk_overlap_size
        #self.separators = ["\n\n", "\n", "(?<=\\. )", " ", ""]
        self.separators = ["\n\n", "\n", "(?<=\\. )"]

    def split_text_with_separators(self, text: str) -> List[str]:
        """
        Splits text based on a series of separators in order, using regular expressions for specific patterns.

        Args:
            text (str): The input text to be split.

        Returns:
            List[str]: A list of split chunks of text based on the separators.
        """
        for sep in self.separators:
            if sep == " ":
                # Handle space as a normal character
                text = text.split(sep)
            else:
                # Handle the regular expressions for new lines and sentences
                text = re.split(sep, text)
            text = [chunk for chunk in text if chunk]  # Remove any empty strings
            text = " ".join(text)  # Rejoin to apply the next separator in the list
        return text.split(" ")  # Final split by spaces

    def generate_chunks(self, txt_files: List[str]) -> List[str]:
        """
        Generates chunks of text from a list of input strings based on chunk size and overlap.

        Args:
            txt_files (List[str]): A list of input text strings to be chunked.

        Returns:
            List[str]: A list of chunked text strings, each chunk being of the defined size, with the specified overlap.
        """
        chunks = []
        for text in txt_files:
            # Step 1: Split the text using separators
            split_text = self.split_text_with_separators(text)

            # Step 2: Create chunks
            start = 0
            while start < len(split_text):
                # Create chunk by joining words/sentences from the split text
                chunk = " ".join(split_text[start:start + self.chunk_size])
                chunks.append(chunk)
                # Move the start point for the next chunk, accounting for overlap
                start += self.chunk_size - self.chunk_overlap_size

        return chunks