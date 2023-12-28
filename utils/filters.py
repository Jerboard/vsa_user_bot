import json

from init import redis_client


def work_chat_filter(chat_id: int) -> bool:
    result = False
    stored_data = redis_client.get('work_chats')
    print(type(stored_data), stored_data)
    if stored_data:
        work_chats = json.loads (stored_data)
        print(work_chats, type(work_chats), type(work_chats[0]))
        if chat_id in work_chats:
            result = True
    return result

work_chat_filter(1)
