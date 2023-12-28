from pyrogram.types import MessageEntity
# from pyrogram.errors.exceptions
from os import getenv
from datetime import datetime, date, time, timedelta

import re
import typing as t

from init import TZ, MY_ID, INVOICE_LINK_NAME, bot
from utils import patterns as p


# определяет упоминания
async def check_mention_in_text(entities: list[MessageEntity], text: str) -> list[str]:
    users = []
    for entity in entities:
        if entity.type == entity.type.TEXT_MENTION:
            users.append(entity.user.id)

        elif entity.type == entity.type.MENTION:
            start = entity.offset + 1
            end = entity.offset + entity.length
            username = text[start:end]
            users.append(username)

    return users


# Проверяет, обращаются ли к боту
def is_call_me(entities: list) -> bool:
    is_me = False
    for user in entities:
        if user == MY_ID:
            is_me = True
            break
    return is_me


# проверяет на запрос задач
def check_tasks_response(text: str) -> bool:
    is_response = False
    target_words = ['задачи', 'мои задачи', 'дедлайны', 'мои дедлайны']
    for word in target_words:
        if text.lower().startswith(word):
            is_response = True
            break
    return is_response


# определяет приоритет
def search_flag_priority(text: str) -> bool:
    priority = False
    target_words = ['важно', 'срочно', 'должны']
    for word in target_words:
        if re.search(word, text, re.IGNORECASE):
            priority = True

    return priority


# ищем дату и время в тексте
def search_deadline(text: str) -> t.Union[datetime, None]:
    # определяет явно заданные дедлайны
    date_match = re.search(p.date_pattern, text)
    if date_match is None:
        date_match = re.search(p.short_date_pattern, text)
    time_match = re.search(p.time_pattern, text)

    target_date = date_match.group().replace('.', '-').replace('/', '-') if date_match else None
    target_time = time_match.group() if time_match else None

    current_date = datetime.now(TZ).date()

    # определяет неявно заданные
    if not target_date:
        # Словарь для соответствия ключевых фраз и смещений дат
        date_triggers = p.get_date_triggers(current_date)

        for phrase, delta_func in date_triggers.items():
            match = re.search(phrase, text, re.IGNORECASE)
            if match:

                # проверяет исключения
                start_slice = match.start() - 7 if match.start() - 7 <= 0 else 0
                end_slice = match.end() + 7
                check_slice = text[start_slice:end_slice]
                except_match = re.match('добры', check_slice, re.IGNORECASE)
                if except_match:
                    return None

                if delta_func == 'days':
                    # delta_days = lambda match: timedelta(days=int(match.group(1)))
                    # delta = delta_days(match)
                    delta = timedelta (days=int (match.group (1)))
                    target_date = current_date + delta

                elif delta_func == 'days_1':
                    day = int(match.group(2))
                    if current_date.day >= day:
                        if current_date.month <= 12:
                            month = current_date.month + 1
                            year = current_date.year
                        else:
                            month = 1
                            year = current_date.year + 1
                        target_date = datetime.strptime(f'{day}-{month}-{year}', '%d-%m-%Y')
                    else:
                        target_date = datetime.strptime(f'{day}-{current_date.month}-{current_date.year}', '%d-%m-%Y')

                elif delta_func == 'on_week':
                    days_until_sunday = 6 - current_date.weekday()
                    target_date = current_date + timedelta(days=days_until_sunday)

                elif delta_func == 'end_month':
                    today = datetime.now(TZ).date()
                    target_date = date(today.year, today.month, 25)
                    if target_date <= current_date:
                        if current_date.month <= 12:
                            month = current_date.month + 1
                            year = current_date.year
                        else:
                            month = 1
                            year = current_date.year + 1
                        target_date = datetime.strptime(f'{25}-{month}-{year}', '%d-%m-%Y')

                else:
                    target_date = current_date + delta_func
                    if target_date <= current_date:
                        target_date = target_date + timedelta(days=7)

    else:
        if len(target_date) == 10:
            target_date = datetime.strptime(target_date, '%d-%m-%Y')
        elif len(target_date) == 8:
            target_date = datetime.strptime(target_date, '%d-%m-%y')
        elif len(target_date) == 5:
            target_date = target_date + f'-{current_date.year}'
            target_date = datetime.strptime(target_date, '%d-%m-%Y')

    # определяет время
    if target_time is None:

        for phrase, deadline_time in p.time_triggers.items():
            match = re.search(phrase, text, re.IGNORECASE)
            if match:
                target_time = deadline_time
    else:
        time_split = str(target_time).split(':')
        target_time = time(int(time_split[0]), int(time_split[1]))

    if target_date or target_time:

        if target_date is None:
            target_date = current_date

        if target_time is None:
            target_time = time(14, 0)
        deadline = datetime.combine(target_date, target_time)
    else:
        deadline = None

    return deadline


# переводит просрок в дни и часы
def get_delay_string(delay_seconds):
    return round(delay_seconds / 86400)


# пробует запросить ссылку
async def get_chat_invite_link(chat_id: int):
    try:
        link_info = await bot.create_chat_invite_link(
            chat_id=chat_id,
            name=INVOICE_LINK_NAME,
            creates_join_request=True
        )
        return link_info.invite_link
    except:
        return 'not_found'
