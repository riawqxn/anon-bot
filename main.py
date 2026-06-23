import asyncio
import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "8733248197:AAHpXAx665wAaXmD1BqJqLXrG39iP3HufgI"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DB ---
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    code TEXT UNIQUE
)
""")
conn.commit()


def get_or_create_code(user_id: int):
    cursor.execute("SELECT code FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if row:
        return row[0]

    code = f"user{user_id}"

    cursor.execute(
        "INSERT INTO users (user_id, code) VALUES (?, ?)",
        (user_id, code)
    )
    conn.commit()

    return code


def get_user_by_code(code: str):
    cursor.execute("SELECT user_id FROM users WHERE code=?", (code,))
    row = cursor.fetchone()
    return row[0] if row else None


# --- START ---
@dp.message(Command("start"))
async def start(message: Message):
    args = message.text.split()

    # якщо це анонімне повідомлення
    if len(args) > 1:
        code = args[1]
        target_id = get_user_by_code(code)

        if target_id:
            text = " ".join(args[2:]) or "💌 нове анонімне повідомлення"
            await bot.send_message(target_id, f"💌 анонім:\n{text}")
            await message.answer("надіслано 💌")
            return

    # звичайний старт
    code = get_or_create_code(message.from_user.id)

    await message.answer(
        "твій анонім-лінк 💌\n\n"
        f"https://t.me/ihatekaddbot?start={code}\n\n"
        "поділись нею і отримуй повідомлення"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
