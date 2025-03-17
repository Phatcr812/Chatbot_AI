import requests

TOGETHER_AI_API_KEY = "API"

TOGETHER_AI_URL = "https://api.together.ai/v1/chat/completions"

def chat_with_ai(user_input, chat_history=[]):
    headers = {
        "Authorization": f"Bearer {TOGETHER_AI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-7b-instruct",
        "messages": chat_history + [{"role": "user", "content": user_input}],
        "temperature": 0.7
    }

    response = requests.post(TOGETHER_AI_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Lỗi khi gọi API AI."
