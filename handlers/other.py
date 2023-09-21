import random

from telebot.types import Message, ReplyKeyboardRemove, CallbackQuery
from telebot.util import extract_arguments, antiflood, extract_command

from bot_core import bot, test_cancel, delete_message_keyboard
from misc import I_DONT_KNOW, STICKERS_404


# ======================================
# ========== Общие методы ==============
# ======================================
@bot.callback_query_handler(func=lambda call: str(call.data).startswith('delete'))
def delete_callback(call: CallbackQuery):
    if call.data == 'delete':
        bot.answer_callback_query(call.id, "Подтверди удаление, это необратимо.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                      reply_markup=delete_message_keyboard(True))
    elif call.data == 'delete_t':
        bot.delete_message(call.message.chat.id, call.message.id)
    else:
        bot.answer_callback_query(call.id, "Ок")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                      reply_markup=delete_message_keyboard(False))


@bot.message_handler(commands=['dice'], auth=True)
def dice_handler(message: Message):
    cnt: str = extract_arguments(message.text)
    if cnt and cnt.isdigit():
        for _ in range(int(cnt)):
            antiflood(bot.send_dice, message.chat.id)
    else:
        bot.send_dice(message.chat.id)


@bot.message_handler(func=lambda m: True, auth=True)
@test_cancel
def all_auth_msg_handler(message: Message):
    if extract_command(message.text) != 'start':
        bot.reply_to(message, I_DONT_KNOW, reply_markup=ReplyKeyboardRemove())
    else:
        bot.reply_to(message, "Мы уже знакомы.", reply_markup=ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: True, auth=False, is_bot=True)
def all_msg_handler(message: Message):
    sticker = random.choice(STICKERS_404)
    bot.send_sticker(message.chat.id, sticker)
