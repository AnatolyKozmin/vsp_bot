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
