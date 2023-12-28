from aiogram import Bot
from aiogram.enums import ParseMode

from os import getenv
from datetime import date

import asyncio
import typing as t


loop = asyncio.get_event_loop()
bot_client = Bot(getenv("CLIENT_TOKEN"), parse_mode=ParseMode.HTML)
