import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import openai

# ------------------------------------------
# Инициализация
# ------------------------------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в .env")
if not OPENAI_API_KEY:
    raise ValueError("❌ Не найден OPENAI_API_KEY в .env")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()

openai.api_key = OPENAI_API_KEY

# ------------------------------------------
# Хэндлеры
# ------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот компании Билдэко.\n"
        "Работаю на aiogram 3 и GPT-5.\n"
        "Задай вопрос или введи команду /help."
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — приветствие\n"
        "/help — помощь\n"
        "Просто напиши вопрос, и я отвечу через GPT."
    )

@router.message(F.text)
async def handle_text(message: Message):
    user_text = message.text.strip()
    await message.answer("⌛ Думаю...")

    try:
        # Асинхронный запрос к OpenAI
        completion = openai.ChatCompletion.create(
            model="gpt-5",  # для GPT-5 (если доступна) или "gpt-4o"
            messages=[
                {"role": "system", "content": "Ты — ассистент компании Билдэко."},
                {"role": "user", "content": user_text},
            ],
            temperature=0.6,
            max_tokens=800,
        )
        reply = completion.choices[0].message.content.strip()
        await message.answer(reply)

    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        await message.answer("⚠️ Ошибка при обращении к OpenAI API.")

# ------------------------------------------
# Основной запуск
# ------------------------------------------
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
