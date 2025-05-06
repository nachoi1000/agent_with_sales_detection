#python app.py
#Clean cache: find . -type d -name "__pycache__" -exec rm -r {} +
from quart import Quart, request, jsonify, send_from_directory
from main import generate_answer
import uuid

app = Quart(__name__)

@app.post("/conversation")
async def create_conversation():
    data = await request.get_json()
    user_input = data.get("user_input")
    conversation_id = str(uuid.uuid4())
    return jsonify({"conversation_id": conversation_id})

@app.post("/message")
async def send_message():
    data = await request.get_json()
    conversation_id = data.get("conversation_id")
    user_input = data.get("user_input")
    result = generate_answer(conversation_id, user_input)
    return jsonify(**result)

# Ruta para servir el frontend
@app.route('/')
async def serve_frontend():
    return await send_from_directory('./frontend', 'index.html')

if __name__ == "__main__":
    app.run()