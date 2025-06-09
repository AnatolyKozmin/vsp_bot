from aiogram import Router, F, types
from aiogram.filters import CommandObject
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Users, Entertainments, Events

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

    # 1. Если reply — ищем по tg_id, если не найдено — по username (с @ и без)
    if message.reply_to_message:
        reply_user = message.reply_to_message.from_user
        # Поиск по tg_id
        user_result = await session.execute(
            select(Users).filter(Users.tg_id == str(reply_user.id))
        )
        target_user = user_result.scalars().first()
        # Если не нашли по tg_id — ищем по username
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

    # 2. Если есть аргумент — ищем по фамилии (fio)
    else:
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) > 1:
            surname = command_parts[1].strip()
            user_result = await session.execute(
                select(Users).filter(Users.fio.ilike(f"%{surname}%"))
            )
            target_user = user_result.scalars().first()

    # 3. Формируем ответ
    if target_user:
        # Форматируем дату рождения
        birthday_str = "—"
        if target_user.birthday:
            try:
                # Если дата хранится как строка "YYYY-MM-DD ..." — берем только дату
                birthday_str = str(target_user.birthday)
                if len(birthday_str) >= 10:
                    birthday_str = birthday_str[:10]
                # Если дата — объект, можно birthday_str = target_user.birthday.strftime("%d.%m.%Y")
            except Exception:
                pass

        # Username всегда с @
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
async def quote_command(message: types.Message):
    if message.reply_to_message and message.reply_to_message.text:
        quote_text = message.reply_to_message.text
        author = message.reply_to_message.from_user.full_name
        # In a real application, you would save this to a database.
        # For now, we'll just acknowledge it.
        response_text = f"Цитата от {author} запечатлена: \"{quote_text}\""
        await message.answer(text=response_text)
    else:
        await message.answer(text="Чтобы запечатлеть цитату, ответьте на сообщение, содержащее цитату.")





@group_router.message(F.text == "!мудрость")
async def wisdom_command(message: types.Message):
    quotes = [
        "Единственный способ делать великие дела — любить то, что ты делаешь. — Стив Джобс",
        "Будьте изменением, которое вы хотите видеть в мире. — Махатма Ганди",
        "Жизнь — это то, что происходит с тобой, пока ты строишь другие планы. — Джон Леннон",
        "Неудача — это просто возможность начать сначала, но уже более мудро. — Генри Форд",
        "Если ты не едешь на вспышку, то ты долбаеб. — Альберт Эйнштейн"
    ]
    import random
    random_quote = random.choice(quotes)
    await message.answer(text=f"Мудрость дня: {random_quote}")





@group_router.message(F.text.startswith("!ринг"))
async def ring_command(message: types.Message):
    if message.reply_to_message:
        target_username = message.reply_to_message.from_user.full_name
        sender_username = message.from_user.full_name
        
        # Simulate a random winner
        import random
        winner = random.choice([sender_username, target_username])
        loser = sender_username if winner == target_username else target_username

        response_text = f"{sender_username} вызывает {target_username} на ринг!\n"
        response_text += f"Победитель: {winner}!\n"
        response_text += f"{loser} улетает в бан на 10 минут (симуляция)."
        
        await message.answer(text=response_text)
    else:
        await message.answer(text="Чтобы выйти на ринг, ответьте на сообщение человека, с которым хотите сразиться.")





@group_router.message(F.text == "!анмут")
async def unban_command(message: types.Message):
    await message.answer(text="Все, кто был выброшен за ринг, возвращены!")





@group_router.message(F.text == "!рулетка")
async def roulette_command(message: types.Message):
    import random
    if random.randint(1, 6) == 1:
        response_text = f"@{(message.from_user.full_name)}, тебе не повезло! Бот банит тебя на 10 минут (симуляция)."
    else:
        response_text = f"@{(message.from_user.full_name)}, тебе повезло! В этот раз обошлось."
    await message.answer(text=response_text)





@group_router.message(F.text == "!кладбище")
async def graveyard_command(message: types.Message):
    # In a real application, this would query a database for banned users.
    # For now, we'll use a placeholder list.
    banned_users = ["Пользователь1", "Пользователь2", "Пользователь3"]
    if banned_users:
        response_text = "Список забаненных в чате:\n" + "\n".join(banned_users)
    else:
        response_text = "В чате нет забаненных пользователей."
    await message.answer(text=response_text)





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
        response_text = f"Я думаю, что \"{text_query}\" больше всего соответствует @{random_user.tg_username} ({random_user.fio})."
    else:
        response_text = "Не могу определить, так как нет пользователей в базе данных."

    await message.answer(text=response_text)





@group_router.message(F.text.startswith("!когда"))
async def when_command(message: types.Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Пожалуйста, укажите событие. Пример: !когда Новый год")
        return

    event_query = command_parts[1].strip()
    
    # This is a placeholder. In a real scenario, you would look up events in a database.
    # For demonstration, we'll provide a generic answer.
    response_text = f"Событие \"{event_query}\" произойдет, когда придет его время. Будьте готовы!"
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
    response_text = f"Вероятность, что {event_query}, составляет {probability}%."
    await message.answer(text=response_text)





@group_router.message(F.text.startswith("!разбудить"))
async def wake_up_command(message: types.Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Пожалуйста, укажите время. Пример: !разбудить YYYY-MM-DD HH:MM:SS")
        return

    datetime_str = command_parts[1].strip()
    # In a real application, you would parse this datetime and schedule a task.
    # For now, we just acknowledge the request.
    response_text = f"Разбудяшка запланирована на {datetime_str}."
    await message.answer(text=response_text)





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
async def wake_up_list_command(message: types.Message):
    # In a real application, this would query a database for scheduled wake-up calls.
    # For now, we'll use a placeholder.
    scheduled_wakeups = [
        "2024-05-03 12:30:00 (для @user1)",
        "2024-05-04 08:00:00 (для @user2)"
    ]
    if scheduled_wakeups:
        response_text = "Список планируемых разбудяшек:\n" + "\n".join(scheduled_wakeups)
    else:
        response_text = "Нет запланированных разбудяшек."
    await message.answer(text=response_text)





@group_router.message(F.text == "!орг дня")
async def org_day_command(message: types.Message):
    # This would typically fetch the organizer from a database or configuration.
    # For now, a placeholder.
    organizer = "Вася Пупкин"
    await message.answer(text=f"Организатор дня Вспышки: {organizer}")





@group_router.message(F.text == "!подскажи")
async def suggest_command(message: types.Message):
    suggestions = [
        "Брось монетку!",
        "Спроси у друга.",
        "Подумай еще раз.",
        "Доверься интуиции.",
        "Сделай перерыв и вернись к этому позже."
    ]
    import random
    response_text = random.choice(suggestions)
    await message.answer(text=f"Бот подсказывает: {response_text}")





@group_router.message(F.text == "!жызнь")
async def life_command(message: types.Message):
    # This would ideally calculate based on user's birthdate from the Users table.
    # For now, a placeholder.
    import datetime
    today = datetime.date.today()
    # Assuming a fixed birthdate for demonstration
    birthdate = datetime.date(1990, 1, 1)
    days_lived = (today - birthdate).days
    await message.answer(text=f"Вы прожили {days_lived} дней.")





@group_router.message(F.text == "!что поесть")
async def what_to_eat_command(message: types.Message):
    food_suggestions = [
        "Пицца",
        "Суши",
        "Борщ",
        "Паста",
        "Салат Цезарь",
        "Шашлык"
    ]
    import random
    response_text = random.choice(food_suggestions)
    await message.answer(text=f"Бот подсказывает, что лучше поесть: {response_text}")





@group_router.message(F.text == "!комплимент")
async def compliment_command(message: types.Message):
    compliments = [
        "Ты сегодня выглядишь потрясающе!",
        "Твоя улыбка озаряет комнату.",
        "Ты очень талантливый человек.",
        "С тобой всегда интересно общаться.",
        "Ты делаешь этот мир лучше."
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
    if message.reply_to_message:
        command_text = message.text.lstrip('!')
        target_username = message.reply_to_message.from_user.full_name
        sender_username = message.from_user.full_name

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
                'наша раша': 'посмотрели Нашу Рашу с'
            }
            declension = action_map.get(command_text, command_text)
            response_text = f"@{target_username}, тебя {declension} (от {sender_username})"
        
        await message.answer(text=response_text)
    else:
        await message.answer(text=f"Чтобы использовать команду {message.text}, ответьте на сообщение человека.")

@group_router.message(F.text.startswith("!нахуй"))
async def nahuy_command(message: types.Message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(text="Пожалуйста, укажите, кого или что послать. Пример: !нахуй работу")
        return
    
    target = command_parts[1].strip()
    response_text = f"Пошел нахуй {target}!"
    await message.answer(text=response_text)
