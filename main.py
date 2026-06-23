```python
import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8733248197:AAGePxPmbpYze_wz7u6Spb9Kwp8iyZcGL5M"

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("bot.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS bans (
    user_id INTEGER PRIMARY KEY
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS links (
    code TEXT PRIMARY KEY,
    owner_id INTEGER
)
""")

conn.commit()


# ---------- MENU ----------
def menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📎 моє посилання", callback_data="link")
    kb.button(text="ℹ️ як це працює", callback_data="help")
    kb.adjust(1)
    return kb.as_markup()


# ---------- START ----------
@dp.message(Command("start"))
async def start(m: Message):
    user_id = m.from_user.id

    cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))

    # генеруємо унікальний код
    code = str(user_id)

    cur.execute("INSERT OR IGNORE INTO links VALUES (?, ?)", (code, user_id))
    conn.commit()

    link = f"https://t.me/{(await bot.get_me()).username}?start={code}"

    await m.answer(
        "привіт 💌\n\n"
        "це твоє анонімне посилання:\n"
        f"{link}\n\n"
        "натисни меню 👇",
        reply_markup=menu()
    )


# ---------- CALLBACK MENU ----------
@dp.callback_query(F.data == "link")
async def link_cb(c: CallbackQuery):
    await c.answer()
    await c.message.answer("твоє посилання вже є в /start 💌")

@dp.callback_query(F.data == "help")
async def help_cb(c: CallbackQuery):
    await c.answer()
    await c.message.answer(
        "як це працює:\n"
        "1. ти даєш посилання\n"
        "2. тобі пишуть анонімно\n"
        "3. ти отримуєш повідомлення тут\n"
        "4. можеш відповідати reply'єм"
    )


# ---------- BAN CHECK ----------
def is_banned(user_id: int):
    cur.execute("SELECT 1 FROM bans WHERE user_id=?", (user_id,))
    return cur.fetchone() is not None


# ---------- ANON MESSAGE HANDLER ----------
@dp.message()
async def handle(m: Message):
    if not m.text and not m.photo and not m.video and not m.voice and not m.document:
        return

    if m.from_user and is_banned(m.from_user.id):
        return

    # якщо це старт з кодом
    if m.text and m.text.startswith("/start"):
        parts = m.text.split()
        if len(parts) == 2:
            code = parts[1]

            cur.execute("SELECT owner_id FROM links WHERE code=?", (code,))
            row = cur.fetchone()

            if row:
                m.from_user.link_owner = row[0]
                await m.answer("напиши своє повідомлення 💌")
            return

    # якщо це звичайне повідомлення → анонімка
    if m.reply_to_message:
        return

    # визначаємо owner (простий варіант)
    cur.execute("SELECT owner_id FROM links WHERE code=?", (str(m.from_user.id),))
    row = cur.fetchone()

    if not row:
        return

    owner_id = row[0]

    # пересилання тексту
    if m.text:
        await bot.send_message(owner_id, f"💌 анонім:\n{m.text}")

    # медіа
    elif m.photo:
        await bot.send_photo(owner_id, m.photo[-1].file_id, caption="💌 анонім фото")

    elif m.video:
        await bot.send_video(owner_id, m.video.file_id, caption="💌 анонім відео")

    elif m.voice:
        await bot.send_voice(owner_id, m.voice.file_id, caption="💌 анонім голосове")

    elif m.document:
        await bot.send_document(owner_id, m.document.file_id, caption="💌 анонім файл")


# ---------- ADMIN COMMANDS ----------
@dp.message(Command("ban"))
async def ban(m: Message):
    if not m.reply_to_message:
        return

    user_id = m.reply_to_message.from_user.id

    cur.execute("INSERT OR IGNORE INTO bans VALUES (?)", (user_id,))
    conn.commit()

    await m.answer("юзера забанено 🚫")


@dp.message(Command("unban"))
async def unban(m: Message):
    if not m.reply_to_message:
        return

    user_id = m.reply_to_message.from_user.id

    cur.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
    conn.commit()

    await m.answer("юзера розбанено ✅")


# ---------- RUN ----------
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```
