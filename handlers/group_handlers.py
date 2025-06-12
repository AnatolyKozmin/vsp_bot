import asyncio
import textwrap
from aiogram import Bot, Router, F, types
from aiogram.filters import CommandObject
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
from datetime import datetime, timedelta
from aiogram.types import InputFile
import random
from aiogram.types import ChatPermissions
from io import BytesIO
from database.models import BeerStats, Mutes, Quotes, Users, Entertainments, Events, WakeUps
from aiogram.types import BufferedInputFile   # ← вместо InputFile
import traceback



BASE_DIR = Path(__file__).resolve().parent.parent   
TEMPLATES_DIR = BASE_DIR / "templates"       


scheduler = AsyncIOScheduler()

group_router = Router()

@group_router.message(F.text.startswith('!уебать'))
async def attack_command(message: types.Message):
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        target_username = message.reply_to_message.from_user.username
        sender_username = message.from_user.first_name
        response_text = f"@{target_username} уебал(а) {sender_username}"
        await message.answer(text=response_text)
    else:
        await message.answer(text="Чтобы использовать команду !уебать, ответьте на сообщение человека, которого хотите 'уебать'.")


@group_router.message(F.text.startswith("!роль"))
async def role_command(message: types.Message, session: AsyncSession):
    # Если ответ на сообщение — ищем по tg_username
    if message.reply_to_message:
        reply_username = message.reply_to_message.from_user.username
        if reply_username:
            if reply_username.startswith('@'):
                reply_username = reply_username[1:]
            user_result = await session.execute(
                select(Users).filter(
                    (Users.tg_username == reply_username) | 
                    (Users.tg_username == f"@{reply_username}")
                )
            )
            user = user_result.scalars().first()
            if user:
                response_text = (
                    f"👤 <b>{user.fio}</b>\n"
                    f"💼 <b>Должность:</b> {user.post or '—'}"
                )
            else:
                response_text = "❌ Пользователь не найден в базе."
            await message.answer(text=response_text, parse_mode="HTML")
            return

    # Проверяем аргумент команды
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(
            text="ℹ️ Используйте:\n"
                 "• <code>!роль &lt;должность&gt;</code> для поиска сотрудников по должности\n"
                 "• <code>!роль &lt;фамилия&gt;</code> для поиска должности сотрудника\n"
                 "• Ответьте на сообщение с <code>!роль</code> для проверки должности"
        )
        return

    query = command_parts[1].strip()

    # 1. Сначала ищем по должностям
    users_by_role = await session.execute(
        select(Users).filter(Users.post.ilike(f"%{query}%"))
    )
    users_list = users_by_role.scalars().all()

    if users_list:
        # Нашли совпадения по должности
        response_text = f"👥 <b>Сотрудники с должностью '{query}':</b>\n\n"
        for user in users_list:
            tg_username = user.tg_username or '—'
            if tg_username != '—' and not tg_username.startswith('@'):
                tg_username = '@' + tg_username
            response_text += f"• {user.fio} ({tg_username})\n"
    else:
        # 2. Если по должности не нашли - ищем по фамилии
        user_by_name = await session.execute(
            select(Users).filter(Users.fio.ilike(f"%{query}%"))
        )
        user = user_by_name.scalars().first()

        if user:
            response_text = (
                f"👤 <b>{user.fio}</b>\n"
                f"💼 <b>Должность:</b> {user.post or '—'}"
            )
        else:
            response_text = "❌ Ничего не найдено. Проверьте правильность написания фамилии или должности."

    await message.answer(text=response_text, parse_mode="HTML")


@group_router.message(F.text.startswith("!инфа"))
async def info_command(message: types.Message, session: AsyncSession):
    target_user = None


    if message.reply_to_message:
        reply_user = message.reply_to_message.from_user

        user_result = await session.execute(
            select(Users).filter(Users.tg_id == str(reply_user.id))
        )
        target_user = user_result.scalars().first()

        if not target_user and reply_user.username:
            username = reply_user.username
            if username.startswith('@'):
                username = username[1:]
            user_result = await session.execute(
                select(Users).filter(
                    (Users.tg_username == username) | (Users.tg_username == f"@{username}")
                )
            )
            target_user = user_result.scalars().first()


    else:
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) > 1:
            surname = command_parts[1].strip()
            user_result = await session.execute(
                select(Users).filter(Users.fio.ilike(f"%{surname}%"))
            )
            target_user = user_result.scalars().first()


    if target_user:

        birthday_str = "—"
        if target_user.birthday:
            try:

                birthday_str = str(target_user.birthday)
                if len(birthday_str) >= 10:
                    birthday_str = birthday_str[:10]

            except Exception:
                pass

        tg_username = target_user.tg_username or '—'
        if tg_username != '—' and not tg_username.startswith('@'):
            tg_username = '@' + tg_username

        response_text = (
            f"👤 <b>{target_user.fio}</b>\n"
            f"📱 <b>Телефон:</b> <code>{target_user.phone_number or '—'}</code>\n"
            f"✉️ <b>Gmail:</b> <code>{target_user.gmail or '—'}</code>\n"
            f"💼 <b>Должность:</b> {target_user.post or '—'}\n"
            f"🎂 <b>День рождения:</b> {birthday_str}\n"
            f"📸 <b>Instagram:</b> {target_user.insta or '—'}\n"
            f"💬 <b>Telegram:</b> {tg_username}\n"
            f"🚇 <b>Метро:</b> {target_user.metro or '—'}"
        )
    else:
        response_text = (
            "❌ <b>Пользователь не найден.</b>\n"
            "Используйте <code>!инфа &lt;фамилия&gt;</code> или ответьте на сообщение пользователя."
        )

    await message.answer(text=response_text, parse_mode="HTML")


@group_router.message(F.text.startswith("!цитата"))
async def quote_command(message: types.Message, session: AsyncSession, bot: Bot):
    if message.reply_to_message and message.reply_to_message.text:
        # Получаем данные о цитате
        quote_text = message.reply_to_message.text
        author = message.reply_to_message.from_user
        added_by = message.from_user
        chat_id = message.chat.id
        added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Пытаемся получить фотографию профиля автора
        photo_path = None
        try:
            user_photos = await bot.get_user_profile_photos(author.id, limit=1)
            if user_photos.total_count > 0:
                # Сохраняем первую фотографию профиля
                photo = user_photos.photos[0][-1]  # Берем фото с максимальным разрешением
                file = await bot.get_file(photo.file_id)
                photo_path = f"profile_photos/{author.id}.jpg"
                await bot.download_file(file.file_path, photo_path)
        except Exception as e:
            photo_path = None  # Если фото не удалось получить, оставляем None

        # Сохраняем цитату в базу данных
        new_quote = Quotes(
            author_id=author.id,
            author_username=author.username,
            author_first_name=author.full_name,
            quote_text=quote_text,
            added_by_id=added_by.id,
            added_at=added_at,
            chat_id=chat_id,
            image_path=photo_path
        )
        session.add(new_quote)
        await session.commit()

        # Генерация изображения с цитатой
        try:
            template_path = TEMPLATES_DIR / "les.jpg"
            if not template_path.exists():
                return await message.answer("❌ Шаблон изображения не найден.")

            image = Image.open(template_path).convert("RGB")
            draw = ImageDraw.Draw(image)

            # Шрифт
            font_path = TEMPLATES_DIR / "Qanelas_ExtraBold.otf"
            if not font_path.exists():
                return await message.answer("❌ Шрифт не найден.")

            quote_font = ImageFont.truetype(font_path, 60)
            author_font = ImageFont.truetype(font_path, 30)

            # Размеры изображения
            image_width, image_height = image.size

            # Аватарка (в виде кружка)
            avatar_y = 50  # Высота аватарки сверху
            if photo_path and Path(photo_path).is_file():
                avatar = Image.open(photo_path).resize((150, 150)).convert("RGB")

                # Создаем маску для кружка
                mask = Image.new("L", (150, 150), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 150, 150), fill=255)

                # Центрируем аватарку
                avatar_x = (image_width - 150) // 2  # Центрируем по горизонтали
                avatar = Image.composite(avatar, Image.new("RGB", (150, 150), (0, 0, 0)), mask)
                image.paste(avatar, (avatar_x, avatar_y), mask)

            # Текст цитаты
            max_width = image_width - 100  # Максимальная ширина текста (с отступами)
            wrapped_text = textwrap.wrap(quote_text, width=40)  # Разбиваем текст на строки

            # Рисуем текст построчно
            text_y = avatar_y + 150 + 50  # Под аватаркой с увеличенным отступом
            for line in wrapped_text:
                text_bbox = draw.textbbox((0, 0), line, font=quote_font)  # Используем textbbox
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = (image_width - text_width) // 2  # Центрируем по горизонтали
                draw.text((text_x, text_y), line, font=quote_font, fill="white")
                text_y += text_height + 10  # Отступ между строками

            # Подпись автора
            author_text = f"— {author.full_name or 'Неизвестный автор'}"
            author_bbox = draw.textbbox((0, 0), author_text, font=author_font)  # Используем textbbox
            author_width = author_bbox[2] - author_bbox[0]
            author_height = author_bbox[3] - author_bbox[1]
            author_x = (image_width - author_width) // 2  # Центрируем по горизонтали
            author_y = image_height - author_height - 50  # Почти в самом низу изображения
            draw.text((author_x, author_y), author_text, font=author_font, fill="white")

            # Отправка изображения
            buf = BytesIO()
            image.save(buf, "JPEG")
            buf.seek(0)
            await message.answer_photo(
                BufferedInputFile(buf.getvalue(), filename="quote.jpg"),
                caption="Ещё одна цитата поймана"
            )

        except Exception as e:
            traceback.print_exc()
            await message.answer("❌ Произошла ошибка при генерации изображения с цитатой.")
    else:
        await message.answer(text="Чтобы запечатлеть цитату, ответьте на сообщение, содержащее цитату.")


@group_router.message(F.text == "!мудрость")
async def wisdom_command(message: types.Message, session: AsyncSession):
    try:
        # 1. Случайная цитата
        result = await session.execute(
            select(Quotes).order_by(func.random()).limit(1)
        )
        quote: Quotes | None = result.scalars().first()
        if quote is None:
            return await message.answer("❌ В базе данных нет цитат.")

        # 2. Шаблон
        template_path = TEMPLATES_DIR / "les.jpg"
        if not template_path.exists():
            return await message.answer("❌ Шаблон изображения не найден.")

        image = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        # 3. Шрифт
        font_path = TEMPLATES_DIR / "Qanelas_ExtraBold.otf"
        if not font_path.exists():
            return await message.answer("❌ Шрифт не найден.")

        quote_font = ImageFont.truetype(font_path, 60)
        author_font = ImageFont.truetype(font_path, 30)

        # Размеры изображения
        image_width, image_height = image.size

        # 4. Аватарка (в виде кружка)
        avatar_y = 50  # Высота аватарки сверху
        if quote.image_path and Path(quote.image_path).is_file():
            avatar = Image.open(quote.image_path).resize((150, 150)).convert("RGB")

            # Создаем маску для кружка
            mask = Image.new("L", (150, 150), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 150, 150), fill=255)

            # Центрируем аватарку
            avatar_x = (image_width - 150) // 2  # Центрируем по горизонтали
            avatar = Image.composite(avatar, Image.new("RGB", (150, 150), (0, 0, 0)), mask)
            image.paste(avatar, (avatar_x, avatar_y), mask)

        # 5. Текст цитаты
        quote_text = quote.quote_text
        max_width = image_width - 100  # Максимальная ширина текста (с отступами)
        wrapped_text = textwrap.wrap(quote_text, width=40)  # Разбиваем текст на строки

        # Рисуем текст построчно
        text_y = avatar_y + 150 + 50  # Под аватаркой с увеличенным отступом
        for line in wrapped_text:
            text_bbox = draw.textbbox((0, 0), line, font=quote_font)  # Используем textbbox
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (image_width - text_width) // 2  # Центрируем по горизонтали
            draw.text((text_x, text_y), line, font=quote_font, fill="white")
            text_y += text_height + 10  # Отступ между строками

        # 6. Подпись автора
        author_text = f"— {quote.author_first_name or 'Неизвестный автор'}"
        author_bbox = draw.textbbox((0, 0), author_text, font=author_font)  # Используем textbbox
        author_width = author_bbox[2] - author_bbox[0]
        author_height = author_bbox[3] - author_bbox[1]
        author_x = (image_width - author_width) // 2  # Центрируем по горизонтали
        author_y = image_height - author_height - 50  # Почти в самом низу изображения
        draw.text((author_x, author_y), author_text, font=author_font, fill="white")

        # 7. Отправка
        buf = BytesIO()
        image.save(buf, "JPEG")
        buf.seek(0)
        await message.answer_photo(
            BufferedInputFile(buf.getvalue(), filename="quote.jpg"),
            caption="Мудрость дня"
        )

    except Exception:
        traceback.print_exc()
        await message.answer("❌ Произошла ошибка при генерации мудрости.")
        

@group_router.message(F.text.startswith("!ринг"))
async def ring_command(message: types.Message, session: AsyncSession):
    # Ваш Telegram username
    bot_creator_username = "yanejettt"

    if not message.reply_to_message:
        await message.answer(
            text="❌ Чтобы выйти на ринг, ответьте на сообщение человека, с которым хотите сразиться."
        )
        return

    challenger = message.from_user
    opponent = message.reply_to_message.from_user

    # Если кто-то пытается вызвать создателя бота
    if opponent.username == bot_creator_username:
        await message.answer(
            text="Правда думаешь, что ты выиграешь?"
        )
        return

    # Проверяем, не замьючен ли вызывающий
    mute_check = await session.execute(
        select(Mutes).filter(
            Mutes.user_id == challenger.id,
            Mutes.is_active == True
        )
    )
    if mute_check.scalars().first():
        await message.answer("❌ Ты в муте, какой ринг?")
        return

    # Создаем интригу
    fight_msg = await message.answer(
        f"⚔️ <b>{challenger.full_name}</b> вызывает на ринг <b>{opponent.full_name}</b>!",
        parse_mode="HTML"
    )
    
    await asyncio.sleep(2)
    await message.answer(text=random.choice(["💥 БУМ НАХУЙ!", "💥 Иииииииууу"]))
    await asyncio.sleep(1)

    # Определяем победителя
    if challenger.username == bot_creator_username:
        winner = challenger
        loser = opponent
    elif opponent.username == bot_creator_username:
        winner = opponent
        loser = challenger
    else:
        winner = random.choice([challenger, opponent])
        loser = opponent if winner == challenger else challenger

    # Создаем мьют для проигравшего
    mute_end = datetime.now() + timedelta(minutes=10)
    new_mute = Mutes(
        user_id=loser.id,
        chat_id=message.chat.id,
        username=loser.username or "No username",
        first_name=loser.full_name,
        mute_start=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        mute_end=mute_end.strftime("%Y-%m-%d %H:%M:%S"),
        reason="Проиграл на ринге",
        is_active=True
    )
    session.add(new_mute)
    await session.commit()

    # Мьютим проигравшего
    try:
        await message.chat.restrict(
            user_id=loser.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=mute_end
        )
        
        final_message = (
            f"🏆 Победитель: <b>{winner.full_name}</b>!\n"
            f"💀 <b>{loser.full_name}</b> отправляется в мут на 10 минут!"
        )
        
        await message.answer(text=final_message, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(
            text="⚠️ Не удалось замьютить проигравшего. Возможно, у бота недостаточно прав."
        )
        # Отменяем запись в БД
        await session.rollback()


@group_router.message(F.text == "!анмут")
async def unban_command(message: types.Message, session: AsyncSession):
    # Получаем всех пользователей с активным мутом в этом чате
    muted_users_result = await session.execute(
        select(Mutes).filter(
            Mutes.is_active == True,
            Mutes.chat_id == message.chat.id
        )
    )
    muted_users = muted_users_result.scalars().all()

    if not muted_users:
        await message.answer("✅ Нет пользователей в муте.")
        return

    from aiogram.types import ChatPermissions

    count = 0
    for mute in muted_users:
        try:
            await message.chat.restrict(
                user_id=mute.user_id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            mute.is_active = False
            count += 1
        except Exception as e:
            continue  # Можно добавить логирование ошибок

    await session.commit()
    await message.answer(f"🔓 Размьючено пользователей: {count}")


@group_router.message(F.text == "!рулетка")
async def roulette_command(message: types.Message, session: AsyncSession):
    special_username = "nikitazin" 

    if message.from_user.username == special_username:
        # Для Никита
        if random.randint(1, 6) == 1:
            response_text = "🎯 Никит, в этот раз судьба злодейка замьютила."
        else:
            response_text = " 🎉 Либо Никит, на этот раз пронесло."
        await message.answer(text=response_text)
        return


    if random.randint(1, 6) == 1:
        mute_end = datetime.now() + timedelta(minutes=10)


        new_mute = Mutes(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            username=message.from_user.username or "Без username",
            first_name=message.from_user.full_name,
            mute_start=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            mute_end=mute_end.strftime("%Y-%m-%d %H:%M:%S"),
            reason="Проиграл в рулетке",
            is_active=True
        )
        session.add(new_mute)
        await session.commit()

        try:
            await message.chat.restrict(
                user_id=message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=mute_end
            )
            response_text = (
                f"🎯 @{message.from_user.username or message.from_user.full_name}, тебе не повезло, брат "
                f"Ты отправлен в мут на 10 минут."
            )
        except Exception as e:

            await session.rollback()
            response_text = (
                f"⚠️ @{message.from_user.username or message.from_user.full_name}, тебе не повезло, брат "
                f"но бот не смог тебя замьютить. Возможно, у него недостаточно прав."
            )
    else:
        response_text = f"🎉 @{message.from_user.username or message.from_user.full_name}, тебе повезло, брат! В этот раз обошлось."

    await message.answer(text=response_text)


@group_router.message(F.text == "!кладбище")
async def graveyard_command(message: types.Message, session: AsyncSession):
    # Получаем всех пользователей с активным мутом в текущем чате
    muted_users_result = await session.execute(
        select(Mutes).filter(
            Mutes.is_active == True,
            Mutes.chat_id == message.chat.id
        )
    )
    muted_users = muted_users_result.scalars().all()

    if muted_users:
        response_text = "💀 <b>Список замьюченных в чате:</b>\n\n"
        for mute in muted_users:
            username = mute.username or "Без имени"
            response_text += f"• {mute.first_name} (@{username}) — до {mute.mute_end}\n"
    else:
        response_text = "✅ В чате нет замьюченных пользователей."

    await message.answer(text=response_text, parse_mode="HTML")


@group_router.message(F.text.startswith("!кто"))
async def who_command(message: types.Message, session: AsyncSession):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Пожалуйста, укажите текст для определения. Пример: !кто самый умный")
        return

    text_query = command_parts[1].strip()
    
    # Fetch all users from the database
    users = await session.execute(select(Users))
    users_list = users.scalars().all()

    if users_list:
        import random
        # For a simple implementation, pick a random user
        # A more complex implementation would involve NLP and similarity matching
        random_user = random.choice(users_list)
        response_text = f"Я думаю, что \"{text_query}\" больше всего соответствует {random_user.tg_username} ({random_user.fio})."
    else:
        response_text = "Не могу определить, так как нет в бд нихуя нет."

    await message.answer(text=response_text)


@group_router.message(F.text.startswith("!когда"))
async def when_command(message: types.Message):
    # Дата события
    event_date = datetime(2025, 8, 8, 0, 0, 0)
    now = datetime.now()

    # Вычисляем разницу
    time_difference = event_date - now

    if time_difference.total_seconds() > 0:
        days_left = time_difference.days
        hours_left = time_difference.seconds // 3600
        minutes_left = (time_difference.seconds % 3600) // 60

        response_text = (
            f"До вспышки осталось:\n"
            f"🗓 {days_left} дней, {hours_left} часов и {minutes_left} минут."
        )
    else:
        response_text = "Вспышка уже наступила!"

    await message.answer(text=response_text)


@group_router.message(F.text.startswith("!вероятность"))
async def probability_command(message: types.Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Пожалуйста, укажите событие. Пример: !вероятность, что пойдет дождь")
        return

    event_query = command_parts[1].strip()
    import random
    probability = random.randint(0, 100)
    response_text = f"Вероятность {event_query} составляет {probability}%."
    await message.answer(text=response_text)


@group_router.message(F.text.startswith("!разбудить"))
async def wake_up_command(message: types.Message, session: AsyncSession, bot: Bot, scheduler: AsyncIOScheduler):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="❌ Пожалуйста, укажите время. Пример: !разбудить YYYY-MM-DD HH:MM:SS")
        return

    datetime_str = command_parts[1].strip()
    try:
        # Парсим дату и время
        wake_up_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        await message.answer(text="❌ Некорректный формат времени. Используйте YYYY-MM-DD HH:MM:SS.")
        return


    wake_up_time = wake_up_time - timedelta(hours=3)  


    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        target_user = message.from_user


    user_result = await session.execute(
        select(Users).filter(Users.tg_id == str(target_user.id))
    )
    user = user_result.scalars().first()
    phone_number = user.phone_number if user else "—"


    new_wake_up = WakeUps(
        user_id=target_user.id,
        username=target_user.username or "Без username",
        first_name=target_user.first_name or "Без имени",
        wake_up_time=wake_up_time,
        chat_id=message.chat.id
    )
    session.add(new_wake_up)
    await session.commit()


    response_text = (
        f"✅ Разбудяшка запланирована для @{target_user.username or target_user.first_name} "
        f"на {wake_up_time.strftime('%Y-%m-%d %H:%M:%S')}.\n"
    )
    await message.answer(text=response_text, parse_mode="HTML")


    async def send_wake_up_message(bot: Bot, chat_id: int, username: str, first_name: str, phone_number: str):
        await bot.send_message(
            chat_id=chat_id,
            text=f"⏰ @{username or first_name}, разбудите брата!\n\n"
                 f"📱 Номер мобилы: <code>{phone_number}</code>",
            parse_mode="HTML"
        )

    scheduler.add_job(
        send_wake_up_message,
        trigger=DateTrigger(run_date=wake_up_time),
        kwargs={
            "bot": bot,
            "chat_id": message.chat.id,
            "username": target_user.username or "Без username",
            "first_name": target_user.first_name or "Без имени",
            "phone_number": phone_number
        }
    )


@group_router.message(F.text.startswith("!не будить"))
async def do_not_wake_up_command(message: types.Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Пожалуйста, укажите время. Пример: !не будить YYYY-MM-DD HH:MM:SS")
        return

    datetime_str = command_parts[1].strip()
    # In a real application, you would cancel the scheduled task.
    # For now, we just acknowledge the request.
    response_text = f"Разбудяшка на {datetime_str} отменена."
    await message.answer(text=response_text)


@group_router.message(F.text == "!разбудяшки")
async def wake_up_list_command(message: types.Message, session: AsyncSession):
    # Получаем все запланированные разбудяшки из базы данных
    wakeups_result = await session.execute(
        select(WakeUps).filter(WakeUps.chat_id == message.chat.id)
    )
    wakeups_list = wakeups_result.scalars().all()

    if wakeups_list:
        response_text = "📅 <b>Список запланированных разбудяшек:</b>\n\n"
        for wakeup in wakeups_list:
            username = wakeup.username or "Без username"
            wake_up_time = wakeup.wake_up_time.strftime("%Y-%m-%d %H:%M:%S")
            response_text += f"• @{username} — {wake_up_time}\n"
    else:
        response_text = "✅ Нет запланированных разбудяшек."

    await message.answer(text=response_text, parse_mode="HTML")


@group_router.message(F.text.startswith("!v"))
async def check_version(message: types.message):
    await message.answer(text='Ver.1.0.8')


@group_router.message(F.text == "!орг дня")
async def org_day_command(message: types.Message, session: AsyncSession):
    # Получаем всех пользователей из таблицы Users
    users_result = await session.execute(select(Users))
    users_list = users_result.scalars().all()

    if not users_list:
        await message.answer("❌ В базе данных нет пользователей.")
        return

    # Выбираем случайного пользователя
    import random
    random_user = random.choice(users_list)
    fio = random_user.fio or "Без имени"
    tg_username = random_user.tg_username or "Без username"

    # Формируем ответ
    response_text = f"👑 Организатор дня Вспышки: <b>{fio}</b> (@{tg_username})"
    await message.answer(text=response_text, parse_mode="HTML")


@group_router.message(F.text == "!подскажи")
async def suggest_command(message: types.Message):
    suggestions = [
        "Забей хуй, брат",
        "Спроси у друга, брат",
        "Подумай еще разб брат",
        "Доверься интуиции, брат",
        "Сделай перерыв и вернись к этому позже, брат",
        "Скоро Vспышка - это Zаебись",
        "Есть киткат, но нет перерыва("
    ]
    import random
    response_text = random.choice(suggestions)
    await message.answer(text=f"{response_text}")


@group_router.message(F.text == "!жызнь")
async def life_command(message: types.Message, session: AsyncSession):
    target_user = None

    if message.reply_to_message:
        reply_username = message.reply_to_message.from_user.username
        if reply_username and reply_username.startswith('@'):
            reply_username = reply_username[1:]
        user_result = await session.execute(
            select(Users).filter(
                (Users.tg_username == reply_username) | 
                (Users.tg_username == f"@{reply_username}")
            )
        )
        target_user = user_result.scalars().first()
    else:
        # Если команда отправлена без ответа, берем данные о пользователе, который написал команду
        sender_username = message.from_user.username
        if sender_username and sender_username.startswith('@'):
            sender_username = sender_username[1:]
        user_result = await session.execute(
            select(Users).filter(
                (Users.tg_username == sender_username) | 
                (Users.tg_username == f"@{sender_username}")
            )
        )
        target_user = user_result.scalars().first()

    if target_user and target_user.birthday:
        try:
            # Парсим дату рождения, учитывая формат "YYYY-MM-DD HH:MM:SS"
            birthday = datetime.strptime(target_user.birthday, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()

            # Считаем количество полных лет, минут и секунд
            years = now.year - birthday.year - ((now.month, now.day) < (birthday.month, birthday.day))
            total_seconds = int((now - birthday).total_seconds())
            total_minutes = total_seconds // 60

            response_text = (
                f"👤 <b>{target_user.fio}</b>\n"
                f"📅 <b>Дата рождения:</b> {birthday.strftime('%d.%m.%Y')}\n"
                f"🎉 <b>Полных лет:</b> {years}\n"
                f"⏳ <b>Прожитых минут:</b> {total_minutes}\n"
                f"⏳ <b>Прожитых секунд:</b> {total_seconds}"
            )
        except ValueError:
            response_text = "❌ Ошибка: некорректный формат даты рождения в базе данных."
    else:
        response_text = "❌ Пользователь не найден или дата рождения отсутствует."

    await message.answer(text=response_text, parse_mode="HTML")


@group_router.message(F.text == "!комплимент")
async def compliment_command(message: types.Message):
    compliments = [
        "Ты сегодня выглядишь потрясающе!",
        "Твоя улыбка озаряет комнату.",
        "Ты очень талантливый человек.",
        "С тобой всегда интересно общаться.",
        "Ты делаешь этот мир лучше.",
        "Ты невероятно добрый человек.",
        "Твои идеи всегда вдохновляют.",
        "Ты настоящий лидер.",
        "Твоя энергия заряжает всех вокруг.",
        "Ты умеешь поддерживать в трудную минуту.",
        "Ты всегда находишь правильные слова.",
        "Твоя харизма притягивает людей.",
        "Ты очень креативный и умный.",
        "Твоя уверенность вдохновляет.",
        "Ты прекрасный друг.",
        "Ты умеешь делать сложное простым.",
        "Твоя доброта не знает границ.",
        "Ты всегда выглядишь стильно.",
        "Ты настоящий профессионал в своем деле.",
        "Ты умеешь создавать уют вокруг себя."
    ]
    import random
    response_text = random.choice(compliments)
    await message.answer(text=f"Комплимент от бота: {response_text}")


@group_router.message(F.text.in_([
    '!уебать', '!обнять', '!секс', '!пожать руку', '!погладить', 
    '!отдать', '!вахта', '!проснуться', '!выпить', '!купаться', 
    '!брызгаться', '!наша раша'
]))
async def interactive_commands(message: types.Message, session: AsyncSession):
    command_text = message.text.lstrip('!')
    sender_username = message.from_user.full_name

    if message.reply_to_message:
        # Если команда отправлена в ответ на сообщение
        target_username = message.reply_to_message.from_user.username or "Без имени"

        # Fetch entertainment data from the database
        entertainment = await session.execute(
            select(Entertainments).filter(Entertainments.name_ent == command_text)
        )
        entertainment = entertainment.scalars().first()

        if entertainment:
            response_text = f"@{target_username}, тебя {entertainment.declension} (от {sender_username})"
        else:
            # Fallback if not found in DB
            action_map = {
                'уебать': 'тебя уебали',
                'обнять': 'тебя обняли',
                'секс': 'с тобой занялись сексом',
                'пожать руку': 'тебе пожали руку',
                'погладить': 'тебя погладили',
                'отдать': 'тебе отдали кое-что',
                'вахта': 'тебя отправили на вахту',
                'проснуться': 'тебя разбудили',
                'выпить': 'с тобой выпили',
                'купаться': 'с тобой искупались',
                'брызгаться': 'тебя обрызгали',
                'наша раша': 'с тобой посмотрели Нашу Рашу'
            }
            declension = action_map.get(command_text, command_text)
            response_text = f"{target_username}, {declension}\n\n{sender_username}"
        
        await message.answer(text=response_text)
    else:
        # Если команда не отправлена в ответ на сообщение
        users_result = await session.execute(select(Users))
        users_list = users_result.scalars().all()

        if not users_list:
            await message.answer("❌ В базе данных нет пользователей.")
            return

        # Выбираем случайного пользователя
        import random
        random_user = random.choice(users_list)
        target_username = random_user.tg_username or "Без имени"

        # Fetch entertainment data from the database
        entertainment = await session.execute(
            select(Entertainments).filter(Entertainments.name_ent == command_text)
        )
        entertainment = entertainment.scalars().first()

        if entertainment:
            response_text = f"{target_username}, тебя {entertainment.declension} {sender_username}"
        else:
            # Fallback if not found in DB
            action_map = {
                'уебать': 'уебали',
                'обнять': 'обняли',
                'секс': 'занялись сексом с',
                'пожать руку': 'пожали руку',
                'погладить': 'погладили',
                'отдать': 'отдали кое-что',
                'вахта': 'отправили на вахту',
                'проснуться': 'разбудили',
                'выпить': 'выпили с',
                'купаться': 'искупали',
                'брызгаться': 'обрызгали',
                'наша раша': 'посмотрели Нашу Рашу с',
                'угостить': 'угостил пивом'
            }
            declension = action_map.get(command_text, command_text)
            response_text = f"@{target_username}, тебя {declension} (от {sender_username})"
        
        await message.answer(text=response_text)


@group_router.message(F.text.startswith("!нахуй"))
async def nahuy_command(message: types.Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Пожалуйста, укажите, кого или что послать. Пример: !нахуй работу")
        return
    
    target = command_parts[1].strip()
    response_text = f"Пошел нахуй {target}!"
    await message.answer(text=response_text)


@group_router.message(F.text.startswith("!выключить бота"))
async def dolbaeb_check(message: types.Message):
    await message.answer('Бля, ты серьёзно ща ?')


@group_router.message(F.text.startswith("!налить пиво"))
async def pour_beer_command(message: types.Message, session: AsyncSession):
    # Убираем лишние пробелы и парсим команду
    command_parts = message.text.strip().split(maxsplit=2)
    target_user = None

    # Определяем, кому налить пиво
    if message.reply_to_message:
        # Если команда отправлена в ответ на сообщение
        target_user = message.reply_to_message.from_user
    elif len(command_parts) > 2:
        # Если указан username
        username = command_parts[2].strip().lstrip('@')
        user_result = await session.execute(
            select(Users).filter(
                (Users.tg_username == username) | (Users.tg_username == f"@{username}")
            )
        )
        target_user = user_result.scalars().first()
    else:
        await message.answer("❌ Укажите, кому налить пиво. Используйте ответ на сообщение или @username.")
        return

    if not target_user:
        await message.answer("❌ Пользователь не найден.")
        return

    # Обновляем или создаем запись в базе данных
    beer_stat = await session.execute(
        select(BeerStats).filter(BeerStats.user_id == target_user.id)
    )
    beer_stat = beer_stat.scalars().first()

    if beer_stat:
        beer_stat.beer_count += 1
        beer_stat.last_poured = datetime.now()
    else:
        beer_stat = BeerStats(
            user_id=target_user.id,
            username=target_user.tg_username or "Без username",
            first_name=target_user.fio or "Без имени",  # Используем правильное поле
            beer_count=1,
            last_poured=datetime.now()
        )
        session.add(beer_stat)

    await session.commit()

    # Формируем ответ
    response_text = (
        f"🍺 Налито пиво для @{target_user.tg_username or target_user.fio}.\n"
        f"Всего кружек: {beer_stat.beer_count}."
    )
    await message.answer(text=response_text)


@group_router.message(F.text == "!топ пива")
async def beer_top_command(message: types.Message, session: AsyncSession):
    # Получаем топ-10 пользователей по количеству выпитого пива
    beer_stats_result = await session.execute(
        select(BeerStats)
        .order_by(BeerStats.beer_count.desc())  # Сортируем по количеству пива (убывание)
        .limit(10)  # Ограничиваем до 10 записей
    )
    top_users = beer_stats_result.scalars().all()

    if not top_users:
        await message.answer("❌ Никто еще не пил пиво. Что за трезвость?")
        return

    # Формируем ответ
    response_text = "🍺 <b>Топ-10 любителей пива:</b>\n\n"
    for idx, user in enumerate(top_users, start=1):
        username = f"@{user.username}" if user.username else user.first_name or "Без имени"
        response_text += f"{idx}. {username} — {user.beer_count} кружек\n"

    # Проверяем, кто на первом месте
    if top_users[0].username == "eqleeq":
        response_text += "\n✅ Всё на своих местах. Арс на первом месте!"
    else:
        response_text += "\n❓Почему не Арс на первом месте? Надо исправлять положение..."

    await message.answer(text=response_text, parse_mode="HTML")


@group_router.message(F.text.contains("брат"))
async def brother_command(message: types.Message):
    # Проверяем, что слово "брат" является отдельным словом
    import re
    if re.search(r"\bбрат\b|\bБрат\b", message.text):
        response_text = "опа братский брат"
        await message.answer(text=response_text)


@group_router.message(F.text.contains("семья" or "семьи"))
async def family_command(message: types.Message):

    import re
    if re.search(r"\bсемья\b|\bсемьи\b|\bсемейные\b|\bсемейный\b", message.text):
        try:
           
            image_path = TEMPLATES_DIR / "dominik.jpg" 
            if not image_path.exists():
                await message.answer("❌ Изображение не найдено.")
                return


            await message.answer_photo(
                BufferedInputFile(image_path.read_bytes(), filename="dominik.jpg"),
            )

        except Exception as e:
            traceback.print_exc()
            await message.answer("❌ Произошла ошибка при обработке изображения.")


@group_router.message(F.text == "!помощь")
async def help_command(message: types.Message):
    response_text = (
        "📜 <b>Список доступных команд:</b>\n\n"
        "<b>Основные команды:</b>\n"
        "• <code>!инфа</code> — Получить информацию о пользователе. Используйте с ответом на сообщение или укажите фамилию.\n"
        "• <code>!цитата</code> — Сохранить цитату. Используйте с ответом на сообщение с текстом.\n"
        "• <code>!мудрость</code> — Получить случайную цитату в виде изображения.\n"
        "• <code>!ринг</code> — Вызвать пользователя на ринг. Используйте с ответом на сообщение.\n"
        "• <code>!анмут</code> — Размьютить всех пользователей в чате.\n"
        "• <code>!рулетка</code> — Рискни и проверь, попадешь ли в мут.\n"
        "• <code>!кладбище</code> — Посмотреть список замьюченных пользователей.\n"
        "• <code>!разбудить YYYY-MM-DD HH:MM:SS</code> — Запланировать разбудяшку для пользователя.\n"
        "• <code>!разбудяшки</code> — Посмотреть список всех запланированных разбудяшек.\n"
        "• <code>!орг дня</code> — Узнать, кто сегодня организатор дня.\n"
        "• <code>!подскажи</code> — Получить случайный совет от бота.\n"
        "• <code>!жызнь</code> — Узнать, сколько минут и секунд прожил пользователь.\n"
        "• <code>!комплимент</code> — Получить случайный комплимент.\n"
        "• <code>!нахуй [текст]</code> — Послать что-то или кого-то нахуй.\n"
        "• <code>!кто [текст]</code> — Узнать, кто больше всего соответствует запросу.\n"
        "• <code>!когда</code> — Узнать, сколько времени осталось до события.\n"
        "• <code>!вероятность [текст]</code> — Узнать вероятность события.\n"
        "• <code>!выключить бота</code> — Проверить, насколько вы серьезны.\n\n"
        
        "<b>Интерактивные команды:</b>\n"
        "• <code>!уебать</code>, <code>!обнять</code>, <code>!секс</code>, <code>!пожать руку</code>, <code>!погладить</code>, и другие — "
        "команды для взаимодействия с пользователями.\n\n"

        "<b>Команды для пива:</b>\n"
        "• <code>!налить пиво</code> — Налить пиво пользователю. Используйте с ответом на сообщение или укажите @username.\n"
        "• <code>!топ пива</code> — Посмотреть топ-10 любителей пива.\n\n"

        "<b>Прочее:</b>\n"
        "• <code>!роль</code> — Узнать должность пользователя или найти сотрудников по должности.\n"
        "• <code>!выключить бота</code> — Команда позволяет выключить бота.\n"
    )
    await message.answer(text=response_text, parse_mode="HTML")