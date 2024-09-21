
class Conversation:
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
