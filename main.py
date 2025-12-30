import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Настройки
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

# Контексты пользователей (в памяти)
user_sessions = {}

# Список разрешённых пользователей (по желанию — ID сотрудников)
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")  # пример: "123456,789012"

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("👋 Привет! Я корпоративный помощник Билдэко.\n"
                         "Задавай вопросы по регламентам, договорам, объектам и процессам.")

@dp.message_handler(commands=["reset"])
async def reset(message: types.Message):
    user_id = str(message.from_user.id)
    user_sessions.pop(user_id, None)
    await message.answer("🔄 Контекст сброшен. Начинаем заново.")

@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    # Ограничение по доступу
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        return await message.answer("⛔ Доступ разрешён только сотрудникам Билдэко.")

    # Создаём контекст, если нет
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": (
                "Ты — корпоративный помощник компании Билдэко. "
                "Отвечай строго по внутренним регламентам и базе знаний компании. "
                "Не выдумывай факты. Если данных нет — пиши: «Недостаточно данных для достоверного ответа.»"
            )}
        ]

    user_sessions[user_id].append({"role": "user", "content": text})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # или gpt-4-turbo
            messages=user_sessions[user_id],
            temperature=0.2
        )
        reply = completion.choices[0].message["content"]
    except Exception as e:
        reply = f"⚠️ Ошибка при запросе к GPT: {e}"

    user_sessions[user_id].append({"role": "assistant", "content": reply})
    await message.answer(reply)

if __name__ == "__main__":
    print("🤖 Бот запущен. Ожидаю сообщения...")
    executor.start_polling(dp)
