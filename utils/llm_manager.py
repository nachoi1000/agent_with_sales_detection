import logging
from pydantic import BaseModel
from storage.vector_db.vectorstore import ChromaVectorStore
import time


class LLMClient:
    def __init__(self, client, base_prompt: str, model: str = "gpt-4o", max_retries: int =3):
        self.client = client
        self.model = model
        self.base_prompt = base_prompt
        self.max_retries = max_retries

    def _handle_response(self, response):
        # Check if 'choices' exists and is not empty
        if not response.choices:
            # If 'choices' is empty, consider it a failed response
            return False

        # If you need to perform additional checks, such as validating the completion reason
        choice = response.choices[0]
        if choice.finish_reason not in ['stop', 'length']:
            # If the reason isn't 'stop' or 'length', it might be an incomplete response
            return False

        return True
    
    
    def chat_completion_response(self, prompt: str, question: str) -> dict:
        """This method receives a formatted prompt and returns the response as a string.
        In this request the prompt is on the content and a question string ."""
        messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question}
            ]
        attempts = 0
        while attempts < self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            except Exception as e:
                logging.error(f"[ERROR] OpenAI request failed: {str(e)}")
                raise
            if self._handle_response(response):
                tokens_input = response.usage.prompt_tokens
                tokens_output = response.usage.completion_tokens
                answer = response.choices[0].message.content
                logging.info(f"chat_completion_response: tokens_input={tokens_input} - tokens_output={tokens_output}")
                return {"answer": answer, "tokens_input": tokens_input, "tokens_output": tokens_output}
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
            try:            
                response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-2024-08-06",
                    messages=messages,
                    response_format=output_format,
                )
            except Exception as e:
                logging.error(f"[ERROR] OpenAI request failed: {str(e)}")
                raise
            if self._handle_response(response):
                tokens_input = response.usage.prompt_tokens
                tokens_output = response.usage.completion_tokens
                answer = response.choices[0].message.parsed
                logging.info(f"chat_completion_response: tokens_input={tokens_input} - tokens_output={tokens_output}")
                return {"answer": answer, "tokens_input": tokens_input, "tokens_output": tokens_output}
            attempts += 1
            time.sleep(2 ** attempts)  # Exponential backoff for retries
        raise Exception(f"Failed after {self.max_retries} retries.")


class Assistant(LLMClient):
    def __init__(self, client, base_prompt, model="gpt-4o", max_retries=3):
        super().__init__(client=client, base_prompt=base_prompt, model=model, max_retries=max_retries)


class RAG(LLMClient):
    def __init__(self, client, vectorstore: ChromaVectorStore, base_prompt: str, model: str = "gpt-4o", max_retries: int = 3):
        super().__init__(client=client, base_prompt=base_prompt, model=model, max_retries=max_retries)
        self.vectorstore = vectorstore
        self.retrieval_strategy = "hybrid_search"

    def get_context(self, question: str, number_of_docs: int = 8) -> str:
        """Retrieves and formats the context."""
        try:
            context_list = self.vectorstore.apply_retrieval_strategy(self.retrieval_strategy, query_texts=[question], n_results=number_of_docs)
            resultado = "/n/n".join(item.get("document") for item in context_list)
            return resultado
        except Exception as e:
            raise Exception("Error trying to retrieve context: {e}")

    def format_prompt(self, context: str) -> str:
        """Format the base_prompt with the given context."""
        return self.base_prompt.replace("{context}", context)
    
