from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import ChatTogether  # Import chatbot đã viết

# Khởi tạo Flask API
app = Flask(__name__)
CORS(app)  # Cho phép Angular gọi API từ domain khác

# Khởi tạo chatbot
chatbot = ChatTogether()

@app.route('/chat', methods=['POST'])
def chat():
    """API nhận tin nhắn từ Angular và trả lời"""
    data = request.json
    user_message = data.get("message", "")
    language_id = data.get("language_id", 1)

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    bot_response = chatbot.chat(user_message, language_id)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
