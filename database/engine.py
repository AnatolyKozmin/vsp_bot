import os
from dotenv import load_dotenv, find_dotenv
load_dotenv()

from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DB_URL = os.getenv('DB_URL')

engine = create_async_engine(DB_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    __abstract__ = True