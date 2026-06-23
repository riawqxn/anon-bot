import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "8733248197:AAGePxPmbpYze_wz7u6Spb9Kwp8iyZcGL5M"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# зберігаємо “лінки”
user_links = {}
anon_links = {}

@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id

    if user_id not in user_links:
        link = f"anon_{user_id}"
        user_links[user_id] = link
        anon_links[link] = user_id

    await message.answer(
        "привіт 💌\n"
        "це твій анонімний бот\n\n"
        f"твоя лінка: {user_links[user_id]}\n\n"
        "напиши повідомлення або використовуй лінку інших"
    )

@dp.message()
async def anon_handler(message: Message):
    user_id = message.from_user.id

    # якщо це відповідь через лінку
    text = message.text or ""

    if text.startswith("anon_"):
        target_id = anon_links.get(text)

        if target_id:
            await bot.send_message(
                target_id,
                f"💌 анонімне повідомлення:\n\n{message.text.replace(text, '')}"
            )
            await message.answer("надіслано 💌")
        else:
            await message.answer("лінку не знайдено ❌")
    else:
        await message.answer("використай /start щоб отримати свою лінку")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
