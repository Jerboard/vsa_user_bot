from pyrogram import Client
from sqlalchemy.ext.asyncio import create_async_engine

import logging
import traceback
import redis
from datetime import datetime

from dotenv import load_dotenv
from os import getenv
from pytz import timezone

import asyncio

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

load_dotenv ()

redis_client = redis.StrictRedis(host=getenv('REDIS_HOST'), port=getenv('REDIS_PORT'), db=0)

TZ = timezone('Europe/Moscow')
ENGINE = create_async_engine(url=getenv('DB_URL_TEST'))
MY_ID = int(getenv('MY_ID'))
FILTER_CHAT_DATA_NAME = getenv('FILTER_CHAT_DATA_NAME')
INVOICE_LINK_NAME = getenv('INVOICE_LINK_NAME')

API_ID = getenv('API_ID')
API_HAS = getenv('API_HAS')

DATETIME_STR_FORMAT = '%d.%m.%y %H:%M'


logging.basicConfig(level=logging.WARNING)


def log_error(message):
    timestamp = datetime.now(TZ)
    filename = traceback.format_exc()[1]
    line_number = traceback.format_exc()[2]
    logging.error(f'{timestamp} {filename} {line_number}: {message}')


bot = Client("vsa")
# bot = Client("vsa", api_id=API_ID, api_hash=API_HAS)

# async def main():
#     async with bot:
#         Send a message, Markdown is enabled by default
        # await bot.send_message("me", "Hi there! I'm using **Pyrogram**")


# bot.run(main())