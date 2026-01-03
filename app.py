from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import jwt, datetime, os, json
from functools import wraps

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

app.config['JSON_AS_ASCII'] = False
SECRET = os.getenv("JWT_SECRET", "supersecret")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Твой ассистент с платформы OpenAI
ASSISTANT_ID = "asst_Qt9Uh3tqhqi7ptyi7ZCuiNWe"

client = OpenAI(api_key=OPENAI_API_KEY)

# 🔐 Временные пользователи
USERS = {
    "79023003355@yandex.ru": {"password": "1234", "role": "Директор"},
    "fin@bldco.ru": {"password": "5678", "role": "Финансовый директор"},
}

# === JWT-декоратор ===
def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Нет токена"}), 401
        try:
            data = jwt.decode(token, SECRET, algorithms=["HS256"])
            return f(data, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"Ошибка токена: {e}"}), 401
    return wrapper


# === Авторизация ===
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")
    user = USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"error": "Неверный логин или пароль"}), 401

    token = jwt.encode({
        "email": email,
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }, SECRET, algorithm="HS256")

    return jsonify({"token": token})


# === Запрос к GPT ===
@app.route("/ask", methods=["POST"])
@token_required
def ask(user):
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Пустой вопрос"}), 400

    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"{user['role']} ({user['email']}): {question}"
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            answer = messages.data[0].content[0].text.value
        else:
            answer = "⚠️ Модель не завершила ответ."

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Веб-интерфейс ===
@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "Buildeco GPT работает ✅"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
