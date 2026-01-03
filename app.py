from flask import Flask, request, jsonify
import jwt, datetime, os
from openai import OpenAI

app = Flask(__name__)
SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
ASSISTANT_ID = "asst_buildeco"  # вставь ID своего ассистента

# 👥 Пример сотрудников (для теста)
USERS = {
    "79023003355@yandex.ru": {"password": "1234", "role": "Директор"},
    "fin@bldco.ru": {"password": "5678", "role": "Финансовый директор"}
}

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# 🔹 Авторизация
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = USERS.get(data.get("email"))
    if not user or user["password"] != data.get("password"):
        return jsonify({"error": "Неверный логин или пароль"}), 401

    payload = {
        "email": data["email"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token})

# 🔹 GPT-запрос
@app.route("/ask", methods=["POST"])
def ask():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Нет токена"}), 401

    try:
        user_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception as e:
        return jsonify({"error": "Ошибка токена"}), 401

    question = request.json["question"]

    # Передаём данные пользователя в GPT
    thread = client.beta.threads.create()
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        instructions=f"Пользователь: {user_data['email']} ({user_data['role']}) задаёт вопрос: {question}"
    )

    # ⚠️ Упрощённо: выводим результат (в реальности можно ждать завершения run)
    return jsonify({"answer": "GPT получил вопрос, ответит после настройки потока."})
