import sqlalchemy as sa
import typing as t

from datetime import datetime

from db.base import METADATA, begin_connection


class ActionRow(t.Protocol):
    id: int
    action_name: str
    comment: str
    speed: datetime


ActionTable = sa.Table(
    'actions',
    METADATA,
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('action_name', sa.String(255)),
    sa.Column('comment', sa.String(128)),
    sa.Column('speed', sa.Float),
)


# добавить действие
async def add_action(action_name: str, comment: str, time_start: datetime) -> None:
    different = datetime.now () - time_start
    speed = float (f'{different.seconds}.{different.microseconds}')
    async with begin_connection () as conn:
        await conn.execute(
            ActionTable.insert ().values (
                action_name=action_name,
                comment=comment,
                speed=speed
            )
        )