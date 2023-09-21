import functools

import telebot
from telebot.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.util import antiflood

from misc import OKAY, TaskState
from db import handler_backend_dao, user_dao
from .filters import BotFilter, AuthFilter, SendToAllFilter, AdminFilter
from misc.consts import BOT_KEY, CAN_DELETE_NOTIF
from .pg_handler_backend import PgHandlerBackend

bot = telebot.TeleBot(BOT_KEY, next_step_backend=PgHandlerBackend(handler_backend_dao), num_threads=6)
bot.add_custom_filter(BotFilter())
bot.add_custom_filter(AuthFilter())
bot.add_custom_filter(SendToAllFilter())
bot.add_custom_filter(AdminFilter())


def test_cancel(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        message: Message = args[0]
        if str(message.text).lower() in ['/cancel', 'отмена', 'прекрати', 'cancel', 'стоп'] \
                or message.text in ['❌', '❌ Отмена', '❌ Выход']:
            bot.send_message(message.chat.id, OKAY, reply_markup=ReplyKeyboardRemove())
            return None
        return func(*args, **kwargs)

    return wrapper_decorator


def call_admin(chat_id):
    bot.send_message(chat_id,
                     "Что-то пошло не так, попробуй еще раз!\nЕсли не помогло, напиши админу")


def delete_message_keyboard(confirm: bool = False):
    keyboard = InlineKeyboardMarkup()
    if not confirm:
        keyboard.add(InlineKeyboardButton(TaskState.get_ico(TaskState.DELETE),
                                          callback_data="delete"))
    else:
        keyboard.add(InlineKeyboardButton(f'{TaskState.get_ico(TaskState.DELETE)} Да',
                                          callback_data="delete_t"),
                     InlineKeyboardButton(f'{TaskState.get_ico(TaskState.DELETE)} Нет',
                                          callback_data="delete_f"))
    return keyboard


def send_message_to_user(chat_id, text, can_delete: bool = False):
    try:
        if can_delete and CAN_DELETE_NOTIF:
            antiflood(bot.send_message, chat_id, text, reply_markup=delete_message_keyboard())
        else:
            antiflood(bot.send_message, chat_id, text)
        return True
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            user_dao.delete(chat_id)
        return False
