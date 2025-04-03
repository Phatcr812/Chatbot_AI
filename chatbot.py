import requests

TOGETHER_AI_API_KEY = "sk-04432f3be2224edf917d2409281e9b6c"

TOGETHER_AI_URL = "https://api.deepseek.com/v1"

def chat_with_ai(user_input, chat_history=[]):
    headers = {
        "Authorization": f"Bearer {TOGETHER_AI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": chat_history + [{"role": "user", "content": user_input}],
        "temperature": 0.7
    }

    response = requests.post(TOGETHER_AI_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Lỗi khi gọi API AI."
