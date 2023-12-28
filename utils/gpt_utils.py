import openai

from os import getenv
from init import log_error


# запрос к чатуГПТ
# async def chatgpt_response(text):
#     gpt_key = getenv('GPT_KEY')
#     # max_tokens = 100
#     temperature = 0.8
#     n = 1
#     openai.api_key = gpt_key
#     content = 'Ты онлайн помощник Василий - отвечаешь в непринуждённом дружеском тоне'
#     messages = [{"role": 'assistant', "content": content}, {"role": 'user', "content": text}]
#     chat_completion = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=messages,
#         temperature=temperature,
#         n=n
#     )
#     return chat_completion['choices'][0]['message']['content'].strip()


async def chatgpt_response(text):
    gpt_key = getenv ('GPT_KEY')

    if not gpt_key:
        return "Ошибка: API-ключ GPT не установлен."

    try:
        openai.api_key = gpt_key
        content = 'Ты онлайн помощник Василий - отвечаешь в непринуждённом дружеском тоне'
        messages = [{"role": 'assistant', "content": content}, {"role": 'user', "content": text}]

        # Выполняем запрос к GPT
        chat_completion = openai.ChatCompletion.create (
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.8,
            n=1
        )

        # Проверяем, что есть ответ от API
        if 'choices' in chat_completion and chat_completion ['choices']:
            return chat_completion ['choices'] [0] ['message'] ['content'].strip ()
        else:
            return "Ошибка: Нет ответа от GPT API."

    except Exception as e:
        log_error(f"Ошибка при взаимодействии с GPT API: {str (e)}")
