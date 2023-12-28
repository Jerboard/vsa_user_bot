import sqlalchemy as sa
import typing as t
import asyncio

from datetime import date

from db.base import METADATA, begin_connection, ChatAdminRow
from .chats import ChatTable


class AdminRow(t.Protocol):
    id: int
    user_id: int
    full_name: str
    username: str
    password: str
    transfer_admin: str
    status: str
    end_date: date


AdminTable = sa.Table(
    'admins',
    METADATA,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('user_id', sa.Integer),
    sa.Column('full_name', sa.String(255)),
    sa.Column('username', sa.String(255)),
    sa.Column('password', sa.String(255)),
    sa.Column('transfer_admin', sa.String(50)),
    sa.Column('status', sa.String(50), default='new'),
    sa.Column('end_date', sa.Date),
)


# инфо
async def get_admin_info(user_id: int, username: str = None) -> AdminRow:
    if username:
        query = AdminTable.select().where(sa.or_(AdminTable.c.user_id == user_id, AdminTable.c.username == username))
    else:
        query = AdminTable.select().where(AdminTable.c.user_id == user_id)
    async with begin_connection () as conn:
        result = await conn.execute (query)
    return result.first()


# инфо а всех чатах админов
async def get_all_admin_chats_info(user_id: int = None) -> tuple[ChatAdminRow]:
    query = (
        sa.select (
            AdminTable.c.id.label ('id_admin_table'),
            AdminTable.c.user_id.label ('admin_user_id'),
            AdminTable.c.full_name.label ('admin_full_name'),
            AdminTable.c.username.label ('admin_username'),
            AdminTable.c.status,
            ChatTable.c.chat_id,
            ChatTable.c.chat_title,
            ChatTable.c.invite_link,
            ChatTable.c.added_at,
        )
        .select_from (AdminTable.join (ChatTable, AdminTable.c.user_id == ChatTable.c.owner_id))
    )

    if user_id:
        query = query.where(AdminTable.c.owner_id == user_id)

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.all()


async def get_all_active_chats() -> list[tuple[int]]:
    query = (
        sa.select (
            ChatTable.c.chat_id.label ('chat_id'),
        )
        .select_from (AdminTable.join (ChatTable, AdminTable.c.user_id == ChatTable.c.owner_id))
    ).where(AdminTable.c.status != 'inactive')

    async with begin_connection () as conn:
        result = await conn.execute (query)

    return result.all()
