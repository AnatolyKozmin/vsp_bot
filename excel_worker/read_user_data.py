import os
import sys 
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.engine import async_session
from database.models import Users
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger(__name__)

async def create_user_data(async_session: AsyncSession):
    try:
        async with async_session() as session: 
            
            count = await session.execute(select(func.count()).select_from(Users))
            if count.scalar() > 0:
                logger.info("Данные уже загружены, ничего не требуется...")
                return 
            
            
            df = pd.read_excel('user_data.xlsx', header=None)
            
            
            if df.empty:
                logger.error("Excel-файл пустой или не содержит данных!")
                raise ValueError("Excel-файл пустой или не содержит данных")
            

            if len(df.columns) < 8:
                logger.error(f"В Excel-файле меньше столбцов, чем ожидалось: {len(df.columns)}")
                raise ValueError(f"Ожидалось 8 столбцов, найдено {len(df.columns)}")
            

            logger.info(f"Количество строк: {len(df)}")
            logger.info(f"Столбцы в DataFrame: {df.columns.tolist()}")
            logger.info(f"Первые строки DataFrame:\n{df.head().to_string()}")


            data = [
                Users(
                    fio=str(row[0]) if pd.notna(row[0]) else "",
                    phone_number=str(row[1]) if pd.notna(row[1]) else "",
                    gmail=str(row[2]) if pd.notna(row[2]) else "",
                    post=str(row[3]) if pd.notna(row[3]) else "",
                    birthday=str(row[4]) if pd.notna(row[4]) else "",
                    insta=str(row[5]) if pd.notna(row[5]) else "",
                    tg_username=str(row[6]) if pd.notna(row[6]) else "",
                    metro=str(row[7]) if pd.notna(row[7]) else "",
                )
                for _, row in df.iterrows()
            ]

            session.add_all(data)
            await session.commit()
            logger.info("Ну тут собственно говоря всё готово")
    except Exception as e: 
        logger.error(f'Че то жесть какая-то произошла, вот такая ошибка братик: {str(e)}')
        async with async_session() as session:
            await session.rollback()
        raise