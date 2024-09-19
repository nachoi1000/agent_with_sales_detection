import uuid

class Conversation:
    def __init__(self, question: str, answer: str, sales_intention: bool = None, consent: bool = None, first_message: bool = False):
        self.id = uuid.uuid4()  # Genera un UUID único
        self.question = question
        self.answer = answer
        self.sales_intention = sales_intention
        self.consent = consent
        self.first_message = first_message

    def __repr__(self):
        return (f"Conversation(id={self.id}, question={self.question}, "
                f"answer={self.answer}, sales_intention={self.sales_intention}, "
                f"consent={self.consent}, first_message={self.first_message})")

class ConversationManager:
    def __init__(self):
        self.conversations = []
        self.conversation_started = False

    def add_message(self, question: str, answer: str, sales_intention: bool = None, consent: bool = None):
        if not self.conversation_started:
            # Marca el primer mensaje
            self.conversations.append(
                Conversation(question=question, answer=answer, sales_intention=sales_intention, consent=consent, first_message=True)
            )
            self.conversation_started = True
        else:
            self.conversations.append(
                Conversation(question=question, answer=answer, sales_intention=sales_intention, consent=consent)
            )

    def get_conversations(self):
        return self.conversations

# Ejemplo de uso
#manager = ConversationManager()

# Agregar mensajes a la conversación
#manager.add_message("Hola, ¿cómo estás?", "¡Hola! Estoy bien, gracias.")
#manager.add_message("¿Qué puedes hacer por mí?", "Puedo ayudarte con varias cosas, como responder preguntas o proporcionar información.")

# Imprimir las conversaciones almacenadas
#for conv in manager.get_conversations():
#    print(conv)