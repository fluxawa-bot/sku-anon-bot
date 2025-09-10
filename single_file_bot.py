# single_file_bot.py
import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Для локальной разработки: положи .env рядом с этим файлом (не пушь .env в GitHub)
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_TOKEN not set. Add it to .env (local) or to Scalingo env vars.")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

WELCOME_TEXT = (
    "👋 Привет, *{name}*!\n"
    "Я — *анонимный чат-бот* для студентов Kozybayev University 🎓\n\n"
    "Здесь можно знакомиться, общаться и находить новых друзей.\n"
    "Нажми «🎯 *Найти собеседника*» — и я соединю тебя с другим студентом.\n\n"
    "⏹ В любой момент можно завершить чат или поиск кнопкой «*Остановить*».\n\n"
    "✨ Удачи и приятных знакомств!"
)

# очередь и пары
waiting = []
active_chats = {}

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎯 Найти собеседника")],
        [KeyboardButton(text="⏹ Остановить")]
    ],
    resize_keyboard=True
)


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    name = message.from_user.first_name or "студент"
    text = WELCOME_TEXT.format(name=name)
    await message.answer(text, reply_markup=main_kb, parse_mode="Markdown")


@dp.message(F.text == "🎯 Найти собеседника")
async def cmd_search(message: Message):
    user_id = message.from_user.id
    if user_id in active_chats:
        await message.answer("❗ Ты уже в чате. Нажми ⏹ Остановить, чтобы выйти.", reply_markup=main_kb)
        return

    if waiting and waiting[0] != user_id:
        partner_id = waiting.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        await bot.send_message(partner_id, "✅ Нашелся собеседник! Можешь писать ✉️", reply_markup=main_kb)
        await message.answer("✅ Нашелся собеседник! Можешь писать ✉️", reply_markup=main_kb)
    else:
        if user_id not in waiting:
            waiting.append(user_id)
            await message.answer("⏳ Ждем собеседника...", reply_markup=main_kb)


@dp.message(F.text == "⏹ Остановить")
async def cmd_stop(message: Message):
    user_id = message.from_user.id
    if user_id in waiting:
        waiting.remove(user_id)
        await message.answer("❌ Поиск остановлен.", reply_markup=main_kb)
        return

    if user_id in active_chats:
        partner_id = active_chats.get(user_id)
        # удаляем пару безопасно
        active_chats.pop(user_id, None)
        if partner_id:
            active_chats.pop(partner_id, None)
            await bot.send_message(partner_id, "❌ Собеседник вышел из чата.", reply_markup=main_kb)
        await message.answer("❌ Ты вышел из чата.", reply_markup=main_kb)
        return

    await message.answer("❗ Ты сейчас не ищешь собеседника и не в чате.", reply_markup=main_kb)


@dp.message()
async def forward_messages(message: Message):
    user_id = message.from_user.id
    if user_id not in active_chats:
        return
    partner_id = active_chats.get(user_id)
    if not partner_id:
        return
    # универсально копируем любое сообщение
    await bot.copy_message(chat_id=partner_id, from_chat_id=message.chat.id, message_id=message.message_id)


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
