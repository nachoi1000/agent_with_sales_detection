from quart import Quart, request, jsonify, send_from_directory
from main import generate_answer
from db.db_manager import MongoDBManager
import uuid

app = Quart(__name__)

MESSAGE_LIMIT = 10  # Set the message limit

@app.post("/conversation")
async def create_conversation():
    data = await request.get_json()
    user_input = data.get("user_input")
    conversation_id = str(uuid.uuid4())

    # Initialize the conversation with a message limit in MongoDB
    MongoDBManager().create_conversation(conversation_id, MESSAGE_LIMIT)
    
    return jsonify({"conversation_id": conversation_id, "remaining_messages": MESSAGE_LIMIT})

@app.post("/message")
async def send_message():
    data = await request.get_json()
    conversation_id = data.get("conversation_id")
    user_input = data.get("user_input")

    # Límite de mensajes de la conversación
    limit_conversation_messages = 10  # Puedes ajustar este valor según sea necesario

    # Calcular los mensajes disponibles
    db_manager = MongoDBManager()
    available_messages = db_manager.get_available_messages(conversation_id, limit_conversation_messages)

    if available_messages > 0:
        # Generar respuesta solo si quedan mensajes disponibles
        answer = generate_answer(conversation_id, user_input, db_manager)
        # Actualizar el conteo después de enviar el mensaje
        return jsonify({"answer": answer, "available_messages": available_messages - 1})
    else:
        return jsonify({"error": "No more messages available in this conversation."})

# Serve frontend
@app.route('/')
async def serve_frontend():
    return await send_from_directory('./frontend', 'index_messages.html')

if __name__ == "__main__":
    app.run()
