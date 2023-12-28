import sqlalchemy as sa
import typing as t

from datetime import datetime

from db.base import METADATA, begin_connection
from init import TZ


class MessageHistoryRow(t.Protocol):
    id: int
    sent_time: datetime
    chat_id: int
    message_id: int
    sender_id: int
    sender_full_name: str
    sender_username: str
    text: str


MessageHistoryTable = sa.Table(
    'message_history',
    METADATA,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('sent_time', sa.DateTime(timezone=True)),
    sa.Column('chat_id', sa.Integer()),
    sa.Column('message_id', sa.Integer()),
    sa.Column('sender_id', sa.Integer()),
    sa.Column('sender_full_name', sa.String(64)),
    sa.Column('sender_username', sa.String(50)),
    sa.Column('text', sa.Text)
)


# добавляет сообщение в историю нового админа
async def add_message_in_history(
        chat_id: int,
        message_id: int,
        sender_id: int,
        sender_full_name: str,
        sender_username: str,
        text: str) -> None:

    payloads = dict (
        sent_time=datetime.now (TZ),
        chat_id=chat_id,
        message_id=message_id,
        sender_id=sender_id,
        sender_full_name=sender_full_name,
        sender_username=sender_username,
        text=text
    )

    async with begin_connection () as conn:
        await conn.execute(MessageHistoryTable.insert().values(payloads))


# отправляет контекст сообщения
async def get_context_message(chat_id: str, message_id: str):
    start_message_id = int(message_id) - 2
    end_message_id = int(message_id) + 3
    async with begin_connection () as conn:
        result = await conn.execute(MessageHistoryTable.select().where(
            sa.and_(
                MessageHistoryTable.c.chat_id == chat_id,
                MessageHistoryTable.c.message_id >= start_message_id,
                MessageHistoryTable.c.message_id <= end_message_id,
                )
            )
        )

    return result.all()
