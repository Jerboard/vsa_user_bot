import os
from pyrogram.filters import new_chat_members
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from datetime import datetime

import db
from init import bot, MY_ID, INVOICE_LINK_NAME
from utils import message_utils as u
from utils.gpt_utils import chatgpt_response
from utils.redis_utils import get_filter_chat_list, add_chat_in_filter

from bot_client import send_messages as sm


@bot.on_message(new_chat_members)
async def check_join_group(client, message: Message):
    my_id = None
    for new_user in message.new_chat_members:
        if new_user.id == MY_ID:
            my_id = new_user.id
            break

    if my_id:
        admin_info = await db.get_admin_info(message.from_user.id)
        if admin_info:
            await db.add_new_chat(
                user_id=message.from_user.id,
                chat_id=message.chat.id,
                chat_title=message.chat.title
            )
            await add_chat_in_filter(message.chat.id)
            await sm.send_admin_add_chat(user_id=message.from_user.id, chat_title=message.chat.title)

        elif message.from_user.id == my_id:
            pass

        else:
            await bot.leave_chat(message.chat.id)


@bot.on_message()
# @bot.on_message(chat(get_filter_chat_list()))
async def hand_message(client, message: Message):
    if message.chat.id not in get_filter_chat_list():
        pass
    else:
        time_start = datetime.now()
        text = message.text if message.text is not None else message.caption
        entities = message.entities if message.entities is not None else message.caption_entities
        sender_full_name = (f'{message.from_user.first_name} '
                            f'{message.from_user.last_name}').replace('None', '').strip ()

        if text is not None:
            mentions = await u.check_mention_in_text (entities, text) if entities else []
            deadline = None

            # определяет обращение к боту запрост в гпт чат
            if u.is_call_me (mentions):
                text = 'Извини, но функция помощника сейчас не доступна('
                await bot.send_message(chat_id=message.chat.id, text=text)
                # gpt_answer = await chatgpt_response (message.text)
                # print(gpt_answer)
                # await message.reply (gpt_answer)

            # # определяет запрос задач для чата, выводит их в личку
            elif u.check_tasks_response (text):
                user_info = db.get_user_info (message.from_user.id)
                if user_info is None:
                    link = f'<a href={os.getenv("START_LINK")}tasks_chat{message.chat.id}>ссылке</a>'
                    text = f'Дружище, не могу написать тебе🤷\n\n' \
                           f'Перейди по {link} и нажми старт, чтоб узнать свои задачи из этого чата'
                    await message.reply (text, parse_mode=ParseMode.HTML)

                else:
                    period = u.search_deadline (text)
                    period = period.date () if period is not None else None

                    await sm.send_user_tasks (
                        user_id=message.from_user.id,
                        chat_id=message.chat.id,
                        status=user_info.status,
                        period=period)

                    await message.reply ('Ответил в личку 😉')

            # проверяет на наличие задач
            else:
                deadline = u.search_deadline (text)
                if deadline is not None:
                    is_reply = True if message.reply_to_message is not None else False

                    if len (mentions) > 0 or is_reply:
                        task_text = message.reply_to_message.text if is_reply else text
                        priority = u.search_flag_priority (text)
                        if is_reply:
                            mentions = [message.reply_to_message.from_user.id, ]

                        for mention in mentions:
                            user = await db.get_user_info (mention)
                            user_id = user.user_id if user else None

                            await db.add_task (
                                chat_id=message.chat.id,
                                message_id=message.id,
                                chat_title=message.chat.title,
                                manager_id=message.from_user.id,
                                manager_name=sender_full_name,
                                assigned=user_id,
                                assigned_username=str(mention),
                                deadline=deadline,
                                task_text=task_text,
                                is_priority=priority)

                            chat_info = await db.get_chat_info(message.chat.id)
                            if not chat_info.invite_link:
                                try:
                                    link_data = await bot.create_chat_invite_link(
                                        chat_id=message.chat.id,
                                        name=INVOICE_LINK_NAME,
                                        creates_join_request=True
                                    )
                                    await db.update_chat_invoice_link(
                                        chat_id=message.chat.id,
                                        link=link_data.invite_link
                                    )
                                except:
                                    pass

            # добавляем запись в историю
            await db.add_message_in_history (
                chat_id=message.chat.id,
                message_id=message.id,
                sender_id=message.from_user.id,
                sender_full_name=sender_full_name,
                sender_username=message.from_user.username,
                text=message.text)

            if deadline:
                name = 'Обработка сообщения с задачей'
            else:
                name = 'Обработка сообщения без задачи'

            await db.add_action (
                action_name=name,
                comment=f'-',
                time_start=time_start
            )