import os
import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

bot = Bot(os.getenv('TOKEN'))

dp = Dispatcher()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())