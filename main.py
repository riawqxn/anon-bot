import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "8733248197:AAGstMN81VsvqOOND8RBdiRSZXNxayR3_xo"

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS bans (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()

# --- MENU ---
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📩 мій профіль")],
        [KeyboardButton(text="🔗 мій лінк")],
        [KeyboardButton(text="🚫 заблокувати/розблокувати (для усіх користувачів)")]
    ],
    resize_keyboard=True
)

# --- HELPERS ---
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


def is_banned(user_id: int):
    cursor.execute("SELECT user_id FROM bans WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None


# --- START ---
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("меню", reply_markup=menu)


# --- PROFILE ---
@dp.message(F.text == "📩 мій профіль")
async def profile(message: Message):
    code = get_or_create_code(message.from_user.id)

    await message.answer(
        f"👤 твій профіль\n\n"
        f"ID: {message.from_user.id}\n"
        f"лінк:\nhttps://t.me/ihatekaddbot?start={code}"
    )


# --- LINK ---
@dp.message(F.text == "🔗 мій лінк")
async def link(message: Message):
    code = get_or_create_code(message.from_user.id)

    await message.answer(
        f"твій анонімний лінк 💌\n"
        f"https://t.me/ihatekaddbot?start={code}"
    )


# --- BAN / UNBAN (простий toggle) ---
@dp.message(F.text == "🚫 заблокувати/розблокувати (для усіх користувачів)")
async def ban_toggle(message: Message):
    user_id = message.from_user.id

    if is_banned(user_id):
        cursor.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
        conn.commit()
        await message.answer("✔ вас розблоковано")
    else:
        cursor.execute("INSERT OR REPLACE INTO bans (user_id) VALUES (?)", (user_id,))
        conn.commit()
        await message.answer("🚫 ви більше не можете надсилати повідомлення.")


# --- HANDLE ANON MESSAGES ---
@dp.message()
async def handle(message: Message):
    if not message.text:
        return

    if message.text.startswith("/"):
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        return

    code = parts[0]
    text = parts[1]

    target_id = get_user_by_code(code)

    if not target_id:
        await message.answer("лінк не знайдено ❌")
        return

    if is_banned(target_id):
        await message.answer("цей користувач заблокував повідомлення 🚫")
        return

    await bot.send_message(
        target_id,
        f"💌 анонім:\n{text}\n\n"
        f"↩ натисни /reply {code}"
    )

    await message.answer("надіслано 💌")


# --- REPLY (імітація чату) ---
@dp.message(Command("reply"))
async def reply(message: Message):
    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        await message.answer("використання: /reply code текст")
        return

    code = args[1]
    text = args[2]

    target_id = get_user_by_code(code)

    if target_id:
        await bot.send_message(
            target_id,
            f"↩ відповідь:\n{text}"
        )

        await message.answer("відповідь надіслано 💬")
    else:
        await message.answer("не знайдено користувача ❌")


# --- RUN ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
