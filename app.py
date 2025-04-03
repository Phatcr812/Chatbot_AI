# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import SimpleChatbot, handle_input
from flask import Response
import json

app = Flask(__name__)
CORS(app)

chatbot = SimpleChatbot()
chat_history = []

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")
    response, _ = handle_input(chatbot, user_message, chat_history)
    return Response(
    json.dumps({"response": response}, ensure_ascii=False),
    mimetype='application/json'
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
