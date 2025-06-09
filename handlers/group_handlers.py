from aiogram import Router, F, types
from aiogram.filters import CommandStart
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Users, Entertainments, Events

group_router = Router()

@group_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(text='Ну че, погнали хули')

