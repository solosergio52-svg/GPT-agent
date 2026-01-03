# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import jwt, datetime, os, json
from functools import wraps

# === Настройки приложения ===
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.getenv("JWT_SECRET", "supersecret")
CORS(app)  # Разрешаем запросы с ai.bldco.ru

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = "asst_Qt9Uh3tqhqi7ptyi7ZCuiNWe"  # ← твой агент на платформе OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# === Тестовые пользователи ===
USERS = {
    "79023003355@yandex.ru": {"password": "1234", "role": "Директор"},
    "fin@bldco.ru": {"password": "5678", "role": "Финансовый директор"}
}

# === JWT-декоратор ===
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Нет токена"}), 401
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            return f(data, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Ошибка авторизации", "detail": str(e)}), 401
    return decorated

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
    }, app.secret_key, algorithm="HS256")

    return jsonify({"token": token})

# === Вопрос к GPT через Assistant API ===
@app.route("/ask", methods=["POST"])
@token_required
def ask(user_data):
    data = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Пустой вопрос"}), 400

    user_email = user_data["email"]
    history_file = f"history/{user_email}.json"

    # Загружаем историю, если есть
    messages = []
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            messages = json.load(f)

    # Создаём новый thread и отправляем вопрос
    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"{user_data['role']} ({user_email}): {question}"
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        if run.status == "completed":
            thread_messages = client.beta.threads.messages.list(thread_id=thread.id)
            answer = thread_messages.data[0].content[0].text.value
        else:
            answer = "⚠️ GPT не завершил ответ."

        # Сохраняем историю
        messages.append({"user": question, "bot": answer})
        os.makedirs("history", exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print("Ошибка GPT:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({"answer": answer})

# === Страница чата ===
@app.route("/chat")
def chat_page():
    return render_template("chat.html")

# === Проверка API ===
@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "Buildeco Assistant API работает ✅"})

# === Запуск приложения ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
