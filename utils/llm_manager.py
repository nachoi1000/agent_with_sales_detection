from pydantic import BaseModel
import time


class LLMClient:
    def __init__(self, client, base_prompt, model="gpt-4o", max_retries=3):
        self.client = client
        self.model = model
        self.base_prompt = base_prompt
        self.max_retries = max_retries

    def _handle_response(self, response):
        # Check if the response code indicates missing password (assuming 401 for this case)
        if response.status_code == 401:
            raise ValueError("Authentication failed. Password missing or incorrect.")

        # Retry if the response is not successful and isn't a password issue
        if response.status_code != 200:
            return False
        
        return True


    def chat_completion_response(self, prompt: str) -> str:
        """This method receives a formatted prompt and returns the response as a string.
        In this request the prompt is on the user."""
        messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        attempts = 0
        while attempts < self.max_retries:
        
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            if self._handle_response(response):
                return response.choices[0].message.content
            
            attempts += 1
            time.sleep(2 ** attempts)   # Exponential backoff for retries
        raise Exception(f"Failed after {self.max_retries} retries.")
    
    
    def assistant_chat_completion_response(self, prompt: str, question: str) -> str:
        """This method receives a formatted prompt and returns the response as a string.
        In this request the prompt is on the content and a question string ."""
        messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question}
            ]
        attempts = 0
        while attempts < self.max_retries:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            if self._handle_response(response):
                return response.choices[0].message.content
            attempts += 1
            time.sleep(2 ** attempts)  # Exponential backoff for retries
        raise Exception(f"Failed after {self.max_retries} retries.")

    
    def chat_completion_structured_response(self, prompt: str, output_format: BaseModel) -> BaseModel:
        """This method receives a formatted prompt and the desired structured output format, and returns a class of the desired structured output format."""
        messages = [
                {"role": "system", "content": "You are an expert at structured data extraction. You will be given unstructured text and should convert it into the given structure."},
                {"role": "user", "content": prompt}
            ]
        attempts = 0
        while attempts < self.max_retries:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=messages,
                response_format=output_format,
            )
            if self._handle_response(completion):
                return completion.choices[0].message.parsed
            attempts += 1
            time.sleep(2 ** attempts)  # Exponential backoff for retries
        raise Exception(f"Failed after {self.max_retries} retries.")


class Assistant(LLMClient):
    def __init__(self, client, base_prompt, model="gpt-4o"):
        super().__init__(client, model)
        self.base_prompt = base_prompt


class RAG(LLMClient):
    def __init__(self, client, vectorstore, base_prompt,model="gpt-4o"):
        super().__init__(client, model)
        self.vectorstore = vectorstore
        self.base_prompt = base_prompt