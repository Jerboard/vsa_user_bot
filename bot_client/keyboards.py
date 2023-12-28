from aiogram.utils.keyboard import InlineKeyboardBuilder


# клавиатура для задач
def get_task_kb(task_id, chat_id, message_id):
    kb = InlineKeyboardBuilder()
    kb.button('📄 Контекст', callback_data=f'context:{chat_id}:{message_id}')
    kb.button('✅ Готово', callback_data=f'close_task:done:{task_id}')
    kb.button('🗑 Отменить', callback_data=f'close_task:cancel:{task_id}')
    kb.button('📆 Перенести', callback_data=f'edit_deadline_1:{task_id}')
    kb.button('❌ Ошибка', callback_data=f'close_task:error:{task_id}')
    return kb.adjust(1, 4)
    # return kb.row(bt1).row(bt2, bt3, bt4, bt5)