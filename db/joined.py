import sqlalchemy as sa
import typing as t

from datetime import datetime, date, timedelta

from init import TZ, log_error
from db.base import METADATA, begin_connection

from db.users import UsersTable, UserRow
from db.admins import AdminTable, AdminRow
from db.chats import ChatTable, ChatRow
from db.message_history import MessageHistoryTable, MessageHistoryRow
from db.tasks import TasksTable, TaskRow


class ChatTaskRow(t.Protocol):
    id: int
    owner_id: int
    chat_id: int
    invite_link: str
    added_at: date
    create_time: datetime
    message_id: int
    chat_title: str
    manager: str
    assigned: int
    assigned_username: str
    deadline: datetime
    task_text: str
    delay: int
    is_priority: bool


async def get_tasks_user(
        user_id: int,
        chat_id: t.Optional [int],
        status: str,
        period: date) -> tuple [ChatTaskRow]:

    query = sa.select(
        TasksTable.c.id,
        TasksTable.c.create_time,
        TasksTable.c.message_id,
        TasksTable.c.chat_title,
        TasksTable.c.manager,
        TasksTable.c.assigned,
        TasksTable.c.assigned_username,
        TasksTable.c.deadline,
        TasksTable.c.task_text,
        TasksTable.c.delay,
        TasksTable.c.is_priority,
        ChatTable.c.owner_id,
        ChatTable.c.chat_id,
        ChatTable.c.invite_link,
        ChatTable.c.added_at,
    ).join (ChatTable, TasksTable.c.chat_id == ChatTable.c.chat_id).where (TasksTable.c.status == 'active').order_by (
        TasksTable.c.is_priority,
        TasksTable.c.chat_id,
        TasksTable.c.deadline.desc ())

    if status == 'user':
        query = query.where(TasksTable.c.assigned == user_id)

    elif status == 'admin':
        query = query.where (ChatTable.c.owner_id == user_id)

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