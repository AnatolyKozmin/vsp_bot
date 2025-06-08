from sqlalchemy import Column, BigInteger, Boolean, ForeignKey, String
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
    
