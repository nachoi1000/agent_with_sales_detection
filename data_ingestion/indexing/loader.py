import os
import pdfplumber
from docx import Document as DocxDocument
import pypandoc  # Make sure pypandoc is installed
from typing import Optional
from data_ingestion.indexing.documents import Document

class LocalLoader:
    def __init__(self, document: Document):
        """
        Initialize the LocalLoader with a Document object.
        
        Args:
            document (Document): The Document object to be loaded with content from the file.
        """
        self.document = document
        self.file_name = os.path.basename(self.document.file_path)
        self.extension = os.path.splitext(self.file_name)[1].lower()

    def load(self):
        """
        Loads content into the provided Document object based on its file extension.
        
        This method detects the file extension and calls the appropriate loader method 
        to read the file content and update the Document object.

        Returns:
            str: The loaded content from the file.
        """
        if self.extension in ['.txt', '.md']:
            return self._load_text()
        elif self.extension == '.pdf':
            return self._load_pdf()
        elif self.extension == '.docx':
            return self._load_docx()
        elif self.extension == '.doc':
            return self._load_doc()
        else:
            raise ValueError(f"Unsupported file type: {self.extension}")

    def _load_text(self) -> str:
        """
        Reads content from a text or markdown file and stores it in the Document object.

        Returns:
            str: The loaded text content.
        """
        with open(self.document.file_path, 'r', encoding='utf-8') as file:
            self.document.content = file.read()
        return self.document.content

    def _load_pdf(self) -> str:
        """
        Reads content from a PDF file and stores it in the Document object.

        Returns:
            str: The loaded PDF content.
        """
        content = ""
        with pdfplumber.open(self.document.file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:  # Only append if text was extracted
                    content += text + "\n"
        self.document.content = content.strip()  # Remove trailing newline
        return self.document.content

    def _load_docx(self) -> str:
        """
        Reads content from a DOCX file and stores it in the Document object.

        Returns:
            str: The loaded DOCX content.
        """
        doc = DocxDocument(self.document.file_path)
        self.document.content = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip() != ""])
        return self.document.content

    def _load_doc(self) -> str:
        """
        Converts and reads content from a DOC file using pypandoc and stores it in the Document object.

        Returns:
            str: The loaded DOC content.
        """
        self.document.content = pypandoc.convert_file(self.document.file_path, 'plain')
        return self.document.content