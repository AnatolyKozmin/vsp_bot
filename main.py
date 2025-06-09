import os
import asyncio
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import select
load_dotenv(find_dotenv())


from database.models import BeerStats
from handlers.group_handlers import group_router, scheduler

from database.engine import async_session
from middleware import DbSessionMiddleware, MuteMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from excel_worker.read_user_data import create_user_data


bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()
dp.include_router(group_router)
dp.message.middleware(DbSessionMiddleware())
dp.message.middleware(MuteMiddleware())
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Создаем экземпляр планировщика
scheduler = AsyncIOScheduler()

# Передаем scheduler в контекст
dp.update.outer_middleware(lambda handler, event, data: data.update(scheduler=scheduler) or handler(event, data))


async def main():
    # Заносим данные
    await create_user_data(async_session)

    # Запускаем планировщик
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(main())