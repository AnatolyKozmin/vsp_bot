from sqlalchemy import Column, BigInteger, Boolean, ForeignKey, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


class Users(Base): 
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fio: Mapped[str] = mapped_column(String)
    phone_number: Mapped[str] = mapped_column(String)
    gmail: Mapped[str] = mapped_column(String)
    post: Mapped[str] = mapped_column(String)
    birthday: Mapped[str] = mapped_column(String)
    insta: Mapped[str] = mapped_column(String)
    tg_username: Mapped[str] = mapped_column(String)
    metro: Mapped[str] = mapped_column(String)
    

class Entertainments(Base):
    __tablename__ = 'entertainments'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_ent: Mapped[str] = mapped_column(String)
    declension: Mapped[str] = mapped_column(String)
    


class Events(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entertam: Mapped[int] = mapped_column(ForeignKey('entertainments.id'))
    who: Mapped[int] = mapped_column(ForeignKey('users.id'))
    whom: Mapped[int] = mapped_column(ForeignKey('users.id'))
    feature: Mapped[int] = mapped_column(Integer, nullable=True)


class Mutes(Base):
    __tablename__ = 'mutes'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger) 
    chat_id: Mapped[int] = mapped_column(BigInteger)  
    username: Mapped[str] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String)
    mute_start: Mapped[str] = mapped_column(String)  
    mute_end: Mapped[str] = mapped_column(String)   
    reason: Mapped[str] = mapped_column(String, nullable=True)  
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  


class Quotes(Base):
    __tablename__ = 'quotes'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(BigInteger)  # Telegram ID автора цитаты
    author_username: Mapped[str] = mapped_column(String, nullable=True)  # Telegram username автора
    author_first_name: Mapped[str] = mapped_column(String)  # Имя автора
    quote_text: Mapped[str] = mapped_column(String)  # Текст цитаты
    added_by_id: Mapped[int] = mapped_column(BigInteger)  # Telegram ID добавившего цитату
    added_at: Mapped[str] = mapped_column(String)  # Дата добавления
    chat_id: Mapped[int] = mapped_column(BigInteger)  # ID чата
    image_path: Mapped[str] = mapped_column(String, nullable=True)  # Путь к фото профиля


class WakeUps(Base):
    __tablename__ = 'wake_ups'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)  # Telegram ID пользователя
    username: Mapped[str] = mapped_column(String)  # Telegram username
    first_name: Mapped[str] = mapped_column(String)  # Имя пользователя
    wake_up_time: Mapped[DateTime] = mapped_column(DateTime)  # Время разбудяшки
    chat_id: Mapped[int] = mapped_column(BigInteger)  # ID чата, где запланирована разбудяшка


class BeerStats(Base):
    __tablename__ = 'beer_stats'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)  # Telegram ID пользователя
    username: Mapped[str] = mapped_column(String)  # Telegram username
    first_name: Mapped[str] = mapped_column(String)  # Имя пользователя
    beer_count: Mapped[int] = mapped_column(Integer, default=0)  # Количество кружек пива
    last_poured: Mapped[DateTime] = mapped_column(DateTime)  # Дата последнего наливания