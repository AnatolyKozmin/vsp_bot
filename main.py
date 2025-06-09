import os
import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from database.engine import async_session

from excel_worker.read_user_data import create_user_data

# bot = Bot(os.getenv('TOKEN'))

# dp = Dispatcher()


async def main():
    await create_user_data(async_session)
    


if __name__ == "__main__":
    asyncio.run(main())