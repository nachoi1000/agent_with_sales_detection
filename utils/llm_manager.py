from pydantic import BaseModel


class LLMClient:
    def __init__(self, client, base_prompt, model="gpt-4o"):
        self.client = client
        self.model = model
        self.base_prompt = base_prompt

    def chat_completion_response(self, prompt: str) -> str:
        """This method receives a formatted prompt and returns the response as a string.
        In this request the prompt is on the user."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    def assistant_chat_completion_response(self, prompt: str, question: str) -> str:
        """This method receives a formatted prompt and returns the response as a string.
        In this request the prompt is on the content and a question string ."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content

    def chat_completion_structured_response(self, prompt: str, output_format: BaseModel) -> BaseModel:
        """This method receives a formatted prompt and the desired structured output format, and returns a class of the desired structured output format."""
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are an expert at structured data extraction. You will be given unstructured text and should convert it into the given structure."},
                {"role": "user", "content": prompt}
            ],
            response_format=output_format,
        )

        return completion.choices[0].message.parsed


class Assistant(LLMClient):
    def __init__(self, client, base_prompt, model="gpt-4o"):
        super().__init__(client, model)
        self.base_prompt = base_prompt


class RAG(LLMClient):
    def __init__(self, client, vectorstore, base_prompt,model="gpt-4o"):
        super().__init__(client, model)
        self.vectorstore = vectorstore
        self.base_prompt = base_prompt