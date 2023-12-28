import sqlalchemy as sa
import typing as t
import logging

from sqlalchemy.sql import func
from datetime import datetime, date, timedelta

from init import TZ
from db.base import METADATA, begin_connection
from utils.message_utils import get_delay_string


class TaskRow(t.Protocol):
    id: int
    create_time: datetime
    status: str
    chat_id: int
    message_id: int
    chat_title: str
    manager: str
    assigned: str
    assigned_username: str
    deadline: datetime
    task_text: str
    delay: int
    is_priority: bool


TasksTable = sa.Table(
    'tasks',
    METADATA,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('create_time', sa.DateTime(timezone=True), default=func.now()),
    sa.Column('status', sa.String(50)),
    sa.Column('chat_id', sa.Integer()),
    sa.Column('message_id', sa.Integer()),
    sa.Column('chat_title', sa.String(255)),
    sa.Column('manager', sa.String(50)),
    sa.Column('manager_name', sa.String(128)),
    sa.Column('assigned', sa.String(50)),
    sa.Column('assigned_username', sa.String(50)),
    sa.Column('deadline', sa.DateTime()),
    sa.Column('task_text', sa.Text()),
    sa.Column('delay', sa.Integer()),
    sa.Column('is_priority', sa.Boolean),
)


# добавить задачу
async def add_task(
        chat_id: int,
        message_id: int,
        chat_title: str,
        manager_id: int,
        manager_name: str,
        assigned: int,
        assigned_username: str,
        deadline: datetime,
        task_text: str,
        is_priority: bool) -> None:

    payloads = dict (create_time=datetime.now (TZ),
                     status='active',
                     chat_id=chat_id,
                     chat_title=chat_title,
                     manager=manager_id,
                     manager_name=manager_name,
                     assigned=assigned,
                     assigned_username=assigned_username,
                     deadline=TZ.localize (deadline),
                     task_text=task_text,
                     is_priority=is_priority,
                     message_id=message_id)

    async with begin_connection () as conn:
        await conn.execute(TasksTable.insert().values(payloads))


# возвращает все задачи пользователя
async def get_tasks_user(user_id: int, chat_id: int, status: str, period: datetime) -> tuple[TaskRow]:
    query = TasksTable.select ().where (TasksTable.c.status == 'active').order_by (
        TasksTable.c.is_priority,
        TasksTable.c.chat_id,
        TasksTable.c.deadline.desc ()
    )

    if status == 'user':
        query = query.where(TasksTable.c.assigned == user_id)

    else:
        query = query.where (TasksTable.c.manager == user_id)

    if chat_id:
        query = query.where(TasksTable.c.chat_id == chat_id)

    if period:
        query = query.where (TasksTable.c.deadline <= period)

    now = datetime.now(TZ)

    delay_query = query.where (TasksTable.c.deadline > now)
    current_query = query.where (TasksTable.c.deadline <= now)

    async with begin_connection () as conn:
        delay_result = await conn.execute(delay_query)
        current_result = await conn.execute(current_query)

    all_tasks = delay_result.all() + current_result.all()
    return all_tasks


# возвращает все задачи для менеджеров из чата
async def get_all_tasks_manager_from_chat(chat_id: int, period: datetime) -> tuple[TaskRow]:
    query = TasksTable.select ().where (
        sa.and_(TasksTable.c.chat_id == chat_id,
                TasksTable.c.status == 'active')).order_by (
        TasksTable.c.is_priority,
        TasksTable.c.deadline.desc ()
    )

    if period:
        query = query.where (TasksTable.c.deadline <= period)

    now = datetime.now (TZ)

    delay_query = query.where (TasksTable.c.deadline > now)
    current_query = query.where (TasksTable.c.deadline <= now)

    async with begin_connection () as conn:
        delay_result = await conn.execute (delay_query)
        current_result = await conn.execute (current_query)

    all_tasks = delay_result.all () + current_result.all ()
    return all_tasks


# список пользователей имеющих дедлайны за период
async def get_users_have_tasks_on_period(target_date: date) -> list:
    async with begin_connection () as conn:
        result = await conn.execute (TasksTable.select().where(TasksTable.c.deadline <= target_date).distinct())

    unique_assigned_users = [task.assigned for task in result.all()]
    return unique_assigned_users


# список менеджеров имеющих дедлайны за период
async def get_managers_have_tasks_on_period(target_date: datetime) -> list:
    async with begin_connection () as conn:
        result = await conn.execute (TasksTable.select().where(TasksTable.c.deadline <= target_date).distinct())

    unique_assigned_users = [task.manager for task in result.all()]
    return unique_assigned_users


# заменить верхние два ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^6
# список менеджеров имеющих дедлайны за период
async def get_have_tasks_on_period(target_date: datetime, status: str) -> list:
    async with begin_connection () as conn:
        result = await conn.execute (TasksTable.select().where(TasksTable.c.deadline <= target_date).distinct())

    if status == 'user':
        return [task.assigned for task in result.all()]
    else:
        return [task.manager for task in result.all ()]


# возвращает все чаты исполнителя
async def get_assigned_chats(user_id: str) -> list:
    async with begin_connection () as conn:
        result = await conn.execute (TasksTable.select().where(TasksTable.c.assigned == user_id).distinct())

    return [task.chat_id for task in result.all()]


# все пользователи получавшие задачи в прошедшем месяце
async def get_all_assigned(weekly=False) -> list:
    query = TasksTable.select ().with_only_columns([TasksTable.c.assigned, TasksTable.c.assigned_username]).distinct ()
    if weekly:
        now = datetime.now (TZ).date ()
        start_date = now - timedelta (days=7)
        query = query.where (sa.and_ (TasksTable.c.deadline >= start_date, TasksTable.c.deadline < now))

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return [[user.assigned, user.assigned_username] for user in result]


# все пользователи получавшие задачи в прошедшем месяце
async def get_top_users_text(weekly=False) -> tuple:
    query = (TasksTable.select().
             with_only_columns([TasksTable.c.assigned_username, func.sum(TasksTable.c.delay)]).
             group_by(TasksTable.c.assigned_username).order_by(func.sum(TasksTable.c.delay)))

    if weekly:
        now = datetime.now(TZ).date()
        start_date = now - timedelta(days=7)
        query = query.where(sa.and_ (TasksTable.c.deadline >= start_date, TasksTable.c.deadline < now))

    async with begin_connection () as conn:
        result = await conn.execute (query)

    top_info = result.all()
    winner = top_info[0].assigned_username
    top_text = ''
    counter = 1
    for row in top_info:
        print(row)
        try:
            # название столбца
            delay = get_delay_string(row[1])
            top_text = top_text + f'{counter}. @{row.assigned_username} - всего просрочено {delay} дней\n'
            counter += 1
        except Exception as ex:
            logging.warning(f'data_func 186 {ex}')

    return top_text, winner


# все пользователи получавшие задачи в прошедшем месяце
async def get_top_users_text_tasks() -> tuple:
    query = TasksTable.select().with_only_columns([TasksTable.c.assigned, TasksTable.c.assigned_username]).distinct()

    async with begin_connection () as conn:
        result = await conn.execute (query)

        all_users = result.all()
        users_info = []
        for user in all_users:
            done_user_tasks = await conn.execute(TasksTable.select().where(
                sa.and_(TasksTable.c.assigned == user.assigned,
                        TasksTable.c.status == 'done')))

            delay_user_tasks = await conn.execute(TasksTable.select().where(TasksTable.c.delay > 0))
            not_delay_user_tasks = await conn.execute(TasksTable.select().where(TasksTable.c.delay == 0))

            users_info.append ({'username': user.assigned_username,
                                'all_tasks': done_user_tasks.count (),
                                'delay': delay_user_tasks,
                                'not_delay': not_delay_user_tasks})

        users_info.sort(key=lambda x: x['all_tasks'], reverse=True)
        winner = users_info[0]['username']
        text = ''
        for user_info in users_info:
            text = f'{text}@{user_info["username"]} - {user_info["all_tasks"]} | {user_info["not_delay"]} | ' \
                   f'{user_info["delay"]}\n'

        return f'Сотрудник - всего | вовремя | с опозданием\n{text}', winner


# статистика для исполнителя
async def get_user_statistic(user_id: str) -> dict:
    base_query = TasksTable.select().where(TasksTable.c.assigned == user_id)

    async with begin_connection () as conn:
        done_tasks = await conn.execute(base_query.where(TasksTable.c.status == 'done'))
        active_tasks = await conn.execute(base_query.where(TasksTable.c.status == 'active'))
        delay_tasks = await conn.execute(base_query.where(TasksTable.c.delay > 0))
        delay_seconds = await conn.execute(base_query.with_only_columns(TasksTable.c.delay))

    return {
        'done_tasks_count': done_tasks.count(),
        'active_tasks_count': active_tasks.count(),
        'delay_tasks_count': delay_tasks.count(),
        'delay': get_delay_string(delay_seconds.sum())
    }


# меняет статус на выполнена
async def make_task_done(task_id: int) -> None:
    query = TasksTable.update ().where (TasksTable.c.id == task_id).values (status='done')

    async with begin_connection () as conn:
        result = await conn.execute(
            TasksTable.select().with_only_columns(TasksTable.c.deadline).where(TasksTable.c.id == task_id))

        deadline = TZ.localize (result.deadline)
        now = datetime.now (TZ)
        delay = now - deadline
        if delay > timedelta (0):
            query = query.values(delay=delay.seconds)

        await conn.execute(query)


# меняет статус на отмена
async def make_task_cancel(task_id: int) -> None:
    async with begin_connection () as conn:
        await conn.execute(TasksTable.update ().where (TasksTable.c.id == task_id).values (status='cancel'))


# меняет статус на ошибка
async def make_task_error(task_id: int) -> None:
    async with begin_connection () as conn:
        await conn.execute(TasksTable.update ().where (TasksTable.c.id == task_id).values (status='error'))


# меняет статус
async def update_task_status(task_id: int, status: str) -> None:
    async with begin_connection () as conn:
        await conn.execute(TasksTable.update ().where (TasksTable.c.id == task_id).values (status=status))


# перенос дедлайна
async def edit_deadline(task_id: int, new_deadline: datetime) -> None:
    async with begin_connection () as conn:
        await conn.execute(TasksTable.update ().where (TasksTable.c.id == task_id).values (deadline=new_deadline))


# добавляет юзернейм нового админа
async def clear_message_history():
    async with begin_connection () as conn:
        result = await conn.execute(
            TasksTable.select().where(TasksTable.c.status == 'active').order_by(TasksTable.c.create_time))
        return result.first()
    # дальше в мессадж хистори


# обновляет таски для юзера если он первый раз
async def update_new_user_tasks(user_id: str, username: str) -> None:
    async with begin_connection () as conn:
        await conn.execute(TasksTable.update().where(TasksTable.c.assigned == username).values(assigned=user_id))
