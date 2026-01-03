from flask import Flask, request, jsonify, render_template, send_from_directory
import jwt, datetime, os
from openai import OpenAI
from functools import wraps

# === Настройки приложения ===
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.getenv("JWT_SECRET", "supersecret")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# === Тестовая база пользователей (можно заменить на 1С/БД) ===
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
            return jsonify({"error": "Требуется авторизация"}), 401
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            return f(data, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Срок действия токена истёк"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Недействительный токен"}), 401
    return decorated


# === Маршрут: проверка API ===
@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "Buildeco Assistant API работает ✅"})


# === Авторизация ===
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"error": "Неверный логин или пароль"}), 401

    token = jwt.encode({
        "email": email,
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }, app.secret_key, algorithm="HS256")

    return jsonify({"token": token})


# === Основной чат-запрос ===
@app.route("/ask", methods=["POST"])
@token_required
def ask(user_data):
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "Не передан вопрос"}), 400

    # Здесь — реальный запрос к OpenAI (можно заменить на Retrieval)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Ты — корпоративный ассистент компании Buildeco. Отвечай профессионально и по-русски."},
                {"role": "user", "content": question}
            ]
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        print("Ошибка GPT:", e)
        return jsonify({"error": "Ошибка при обращении к GPT"}), 500

    return jsonify({
        "answer": f"Ответ для {user_data['role']} ({user_data['email']}):\n\n{answer}"
    })


# === Маршрут страницы чата (ChatGPT UI) ===
@app.route("/chat")
def chat_page():
    return render_template("chat.html")


# === Главная страница (можно сделать redirect на Тильду) ===
@app.route("/")
def home():
    return jsonify({"message": "Buildeco Assistant API"})


# === Запуск приложения ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
