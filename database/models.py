from sqlalchemy import Column, BigInteger, Boolean, ForeignKey, String, Integer
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
    author_id: Mapped[int] = mapped_column(BigInteger) 
    author_username: Mapped[str] = mapped_column(String, nullable=True) 
    author_first_name: Mapped[str] = mapped_column(String)  
    quote_text: Mapped[str] = mapped_column(String)  
    added_by_id: Mapped[int] = mapped_column(BigInteger)  
    added_at: Mapped[str] = mapped_column(String)  
    chat_id: Mapped[int] = mapped_column(BigInteger)  
    image_path: Mapped[str] = mapped_column(String, nullable=True)  