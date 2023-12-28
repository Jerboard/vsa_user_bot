from datetime import datetime, date

import db
from init import TZ, log_error, DATETIME_STR_FORMAT
from bot_client.base import bot_client as bot
from bot_client import keyboards as kb


# отправляет список задач
async def send_user_tasks(user_id: int, chat_id: int, status: str, period: date = None) -> None:
    time_start = datetime.now()
    if user_id == chat_id:
        chat_id = None

    tasks = await db.get_tasks_user(
        user_id=user_id,
        chat_id=chat_id,
        status=status,
        period=period)

    if not tasks:
        if chat_id:
            # chat = await bot.get_chat (chat_id)
            chat = await db.get_chat_info(chat_id)
            text = f'У вас нет текущих задач в чате {chat.chat_title}'
        else:
            text = 'У вас нет текущих задач'
        await bot.send_message(user_id, text)

    else:
        for task in tasks:
            priority_flag = '' if task.is_priority is False else '‼️'

            now = datetime.now(TZ)
            if TZ.localize(task.deadline) < now:
                priority_flag = priority_flag + ' ⏰'
                text = f'<b>{task.task_text}</b>'
            else:
                text = task.task_text

            deadline_string = task.deadline.strftime(DATETIME_STR_FORMAT)
            time_add = task.create_time.strftime(DATETIME_STR_FORMAT)

            # if message_link != 'not_found':
            if task.invite_link:
                chat_name = f'<a href="{task.invite_link}">{task.chat_title}</a>'
            else:
                chat_name = task.chat_title

            if status == 'user':
                text = f'{priority_flag}\n' \
                       f'<b>Чат:</b> {chat_name}\n' \
                       f'<b>Поставлена:</b> {time_add}\n' \
                       f'<b>Дедлайн:</b> {deadline_string}\n\n' \
                       f'{text}'
            else:

                text = f'{priority_flag}\n' \
                       f'<b>Чат:</b> {chat_name}\n' \
                       f'<b>Поставлена:</b> {time_add}\n' \
                       f'<b>Дедлайн:</b> {deadline_string}\n' \
                       f'<b>Ответственный:</b> @{task.assigned_username}\n\n' \
                       f'{text}'

            try:
                if str(user_id).isdigit():
                    await bot.send_message(chat_id=user_id,
                                           text=text,
                                           disable_web_page_preview=True,
                                           reply_markup=kb.get_task_kb(task.id, task.chat_id, task.message_id))
                else:
                    log_error(f'dont send message on user {user_id}')

            except Exception as ex:
                log_error(ex)

    await db.add_action (
        action_name='Просмотр задач ЮБ',
        comment=str (len (tasks)),
        time_start=time_start
    )


# отправляет сообщение админу с напоминанием
async def send_admin_add_chat(user_id: int, chat_title: str):
    text = (f'Бот добавлен в чат {chat_title}\n\n'
            f'Не забудьте дать права администратора боту. '
            f'Это нужно только для того, чтоб бот мог предоставлять сотрудникам ссылку на чат. '
            f'Ссылка будет показана только сотрудникам уже состоящим в чате')

    await bot.send_message(chat_id=user_id, text=text)
