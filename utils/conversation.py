from abc import ABC, abstractmethod

class BaseConversation(ABC):
    @abstractmethod
    def to_dict(self):
        pass

class Conversation(BaseConversation):
    def __init__(self, conversation_id: str, question: str, answer: str, sales_intention: bool = None, consent: bool = None):
        self.conversation_id = conversation_id  
        self.question = question
        self.answer = answer
        self.sales_intention = sales_intention
        self.consent = consent

    def __repr__(self):
        return (f"Conversation(id={self.conversation_id}, question={self.question}, "
                f"answer={self.answer}, sales_intention={self.sales_intention}, "
                f"consent={self.consent})")

    def to_dict(self):
        return {
            'conversation_id': self.conversation_id,
            'question': self.question,
            'answer': self.answer,
            'sales_intention': self.sales_intention,
            'consent': self.consent
        }


class ConversationForSales(BaseConversation):
    def __init__(self, conversation_id: str, name: str, email: str, conversation: list[str]):
        self.conversation_id = conversation_id  
        self.name = name
        self.email = email
        self.conversation = conversation

    def __repr__(self):
        return (f"Conversation(id={self.conversation_id}, name={self.name}, "
                f"email={self.email}, conversation={self.conversation})")

    def to_dict(self):
        return {
            'conversation_id': self.conversation_id,
            'name': self.name,
            'email': self.email,
            'conversation': self.conversation
        }
