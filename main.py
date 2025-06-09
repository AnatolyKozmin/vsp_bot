import os
import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from handlers.group_handlers import group_router

from database.engine import async_session
from middleware import DbSessionMiddleware

from excel_worker.read_user_data import create_user_data


bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()
dp.include_router(group_router)
dp.message.middleware(DbSessionMiddleware())


async def main():
    # заносим данные
    await create_user_data(async_session)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(main())