import typing as t
import sqlalchemy as sa

from datetime import date
from sqlalchemy.ext.asyncio import AsyncConnection

from init import ENGINE

METADATA = sa.MetaData()


def begin_connection() -> t.AsyncContextManager[AsyncConnection]:
    return ENGINE.begin()


async def init_models():
    async with ENGINE.begin() as conn:
        await conn.run_sync(METADATA.create_all)


class ChatAdminRow(t.Protocol):
    id_admin_table: int
    admin_user_id: int
    admin_full_name: str
    admin_username: str
    status: str
    end_date: date
    chat_id: int
    title: str
    invite_link: str
    added_at: date