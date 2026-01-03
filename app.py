from flask import Flask, request, jsonify
import jwt, datetime, os
from openai import OpenAI

# === Настройки приложения ===
app = Flask(__name__)
SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")  # секрет для JWT
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")         # ключ OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ID твоего ассистента (из platform.openai.com → Assistants)
ASSISTANT_ID = "asst_buildeco"

# === Временная база пользователей ===
USERS = {
    "79023003355@yandex.ru": {"password": "1234", "role": "Директор"},
    "fin@bldco.ru": {"password": "5678", "role": "Финансовый директор"}
}

# === CORS-разрешения (для запросов с Tilda) ===
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"  # можно ограничить ai.bldco.ru
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# === 1. Проверка работы API ===
@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "Buildeco Assistant API работает ✅"})


# === 2. Авторизация (вход) ===
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # Проверяем пользователя
    user = USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"error": "Неверный логин или пароль"}), 401

    # Генерируем JWT-токен
    payload = {
        "email": email,
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token})


# === 3. Чат-запрос к GPT ===
@app.route("/ask", methods=["POST"])
def ask():
    # Проверка токена
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Нет токена"}), 401

    try:
        user_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Срок действия токена истёк"}), 401
    except Exception:
        return jsonify({"error": "Неверный токен"}), 401

    # Получаем вопрос
    data = request.json
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Пустой запрос"}), 400

    # Отправляем вопрос в OpenAI Assistant
    try:
        thread = client.beta.threads.create()
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
            instructions=f"Пользователь: {user_data['email']} ({user_data['role']}). Вопрос: {question}"
        )

        # ⚙️ Упрощённо — сразу возвращаем ответ-заглушку
        # (можно расширить, чтобы дожидаться завершения run)
        return jsonify({
            "answer": f"Вопрос получен от {user_data['role']} ({user_data['email']}): {question}\n"
                      f"Обработка в GPT выполняется..."
        })
    except Exception as e:
        return jsonify({"error": f"Ошибка при обращении к GPT: {str(e)}"}), 500


# === 4. Точка входа для Render ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
