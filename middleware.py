from aiogram.dispatcher.middlewares.base import BaseMiddleware
from database.engine import async_session


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session() as session:
            data['session'] = session
            return await handler(event, data)
        

