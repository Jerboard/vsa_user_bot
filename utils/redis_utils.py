import json

from init import redis_client, FILTER_CHAT_DATA_NAME
from db.admins import get_all_active_chats


# добавляет чат в фильтр
async def add_chat_in_filter(chat_id: int) -> None:
    stored_data = redis_client.get (FILTER_CHAT_DATA_NAME)
    chats: list = json.loads (stored_data)
    chats.append(chat_id)
    redis_client.set (FILTER_CHAT_DATA_NAME, json.dumps (chats))


# возвращает список чатов
def get_filter_chat_list() -> list:
    stored_data = redis_client.get (FILTER_CHAT_DATA_NAME)
    if stored_data:
        return json.loads (stored_data)
    else:
        return []



# пишет данные в редис
def save_redis_data(data_name: str, data: dict) -> None:
    redis_client.set (data_name, json.dumps (data))


# извлекает данные
def get_redis_data(data_name: str):
    stored_data = redis_client.get (data_name)
    return json.loads (stored_data)
