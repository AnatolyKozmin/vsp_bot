import os
import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from database.engine import async_session
from middleware import DbSessionMiddleware

from excel_worker.read_user_data import create_user_data


bot = Bot(os.getenv('TOKEN'))

dp = Dispatcher()
dp.message.middleware(DbSessionMiddleware)

async def main():
    # зантсим данные
    await create_user_data(async_session)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(main())