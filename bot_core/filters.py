from telebot.custom_filters import SimpleCustomFilter
from telebot.types import Message

from db import user_dao


class BotFilter(SimpleCustomFilter):
    key = 'is_bot'

    def check(self, message: Message):
        return message.chat.type == "private"


class AuthFilter(SimpleCustomFilter):
    key = 'auth'

    def check(self, message: Message):
        return message.chat.type == "private" and user_dao.user_exists(message.from_user.id)


class SendToAllFilter(SimpleCustomFilter):
    key = 'send_to_all'

    def check(self, message: Message):
        return message.chat.type == "private" \
            and user_dao.user_exists(message.from_user.id) \
            and bool(user_dao.get_user_info(message.from_user.id)['can_post'])


class AdminFilter(SimpleCustomFilter):
    key = 'admin'

    def check(self, message: Message):
        return message.chat.type == "private" \
            and user_dao.user_exists(message.from_user.id) \
            and bool(user_dao.get_user_info(message.from_user.id)['is_admin'])
