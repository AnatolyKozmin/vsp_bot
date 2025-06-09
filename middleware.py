from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from sqlalchemy import select

from datetime import datetime

from database.engine import async_session
from database.models import Mutes


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session() as session:
            data['session'] = session
            return await handler(event, data)


class MuteMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data):
        if isinstance(event, types.Message):
            session = data['session']
            
            # Проверяем, не в муте ли пользователь
            mute = await session.execute(
                select(Mutes).filter(
                    Mutes.user_id == event.from_user.id,
                    Mutes.is_active == True,
                    Mutes.chat_id == event.chat.id
                )
            )
            mute = mute.scalars().first()
            
            if mute:
                # Проверяем, не истек ли мьют
                mute_end = datetime.strptime(mute.mute_end, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > mute_end:
                    # Мьют истек, деактивируем
                    mute.is_active = False
                    await session.commit()
                else:
                    # Удаляем сообщение
                    await event.delete()
                    return
                    
        return await handler(event, data)
        

