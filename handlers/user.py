import datetime
import re

from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telebot.util import extract_arguments, antiflood

from bot_core import bot, test_cancel
from db import user_dao
from misc import CHAT_PASSWORD_URL, CHAT_PASSWORD, rus_day, OKAY, I_DONT_KNOW, time_to_str, TIME_RE, list_split, \
    login_to_str


# ======================================
# ====== Регистрация пользователя ======
# ======================================
@bot.message_handler(commands=['start'], auth=False)
def start_handler(message: Message):
    if CHAT_PASSWORD_URL in extract_arguments(message.text):
        user_dao.add(message.from_user.id, message.from_user.full_name, message.from_user.username)
        bot.send_message(message.chat.id, f"Добро пожаловать {message.from_user.full_name}")
    else:
        bot.send_message(message.chat.id, "Приветствую тебя путник! Скажи пароль.")
        bot.register_next_step_handler(message, start_handler_step2)


def start_handler_step2(message: Message, try_cnt=1):
    if CHAT_PASSWORD.casefold() in message.text.replace('+', ' ').casefold():
        user_dao.add(message.from_user.id, message.from_user.full_name, message.from_user.username)
        bot.send_message(message.chat.id, f"Добро пожаловать {message.from_user.full_name}")
    else:
        if try_cnt < 3:
            bot.reply_to(message, "Это не верный пароль. Попробуй еще раз.")
            bot.register_next_step_handler(message, start_handler_step2, try_cnt=try_cnt + 1)
        else:
            bot.reply_to(message, "Это не верный пароль. Отправь команду /start, чтобы попробовать еще раз.")


# ======================================
# ====== Настройки пользователя ========
# ======================================
@bot.message_handler(commands=['settings'], auth=True)
def settings_handler(message: Message):
    settings = user_dao.get_user_info(message.from_user.id)
    msg = f"Настройки:\n" \
          f"\t🔹 Напоминания - {'Включены' if settings['notif_enable'] else 'Выключены'}.\n" \
          f"\t🔹 Время напоминаний - в {time_to_str(settings['notif_time'])}\n" \
          f"\t🔹 Первое напоминание - за {settings['first_notif_days']} {rus_day(settings['first_notif_days'])}.\n" \
          f"\t🔹 Второе напоминание - за {settings['second_notif_days']} {rus_day(settings['second_notif_days'])}.\n" \
          f"\t🔹 Надписи на кнопках - {'Включены' if not settings['small_btn'] else 'Выключены'}.\n" \
          f"Что хотите изменить?"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Напоминания", "Время напоминаний", "Первое напоминание", "Второе напоминание", "Надписи на кнопках",
                 "ㅤ", "Отмена", row_width=2)
    bot.send_message(message.chat.id, msg, reply_markup=keyboard)
    bot.register_next_step_handler(message, settings_handler_step2)


@test_cancel
def settings_handler_step2(message: Message):
    if message.text == "Напоминания":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Включить", "Выключить", row_width=2)
        bot.send_message(message.chat.id, "Включить / Выключить", reply_markup=keyboard)
        bot.register_next_step_handler(message, settings_handler_step_notif)
    elif message.text == "Время напоминаний":
        bot.send_message(message.chat.id, "Во сколько присылать напоминания?\n"
                                          "Время в формате чч:мм (Например 16:30)\n"
                                          "Я буду присылать напоминание в это время ±5 минут",
                         reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, settings_handler_step_notif_time)
    elif message.text == "Первое напоминание":
        bot.send_message(message.chat.id, "За сколько дней напомнить в первый раз? [0 - для отключения]",
                         reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, settings_handler_step_notif_days, step_type="first")
    elif message.text == "Второе напоминание":
        bot.send_message(message.chat.id, "За сколько дней напомнить во второй раз? [0 - для отключения]",
                         reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, settings_handler_step_notif_days, step_type="second")
    elif message.text == "Надписи на кнопках":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Включить", "Выключить", row_width=2)
        bot.send_message(message.chat.id, "Включить / Выключить", reply_markup=keyboard)
        bot.register_next_step_handler(message, settings_handler_step_btn)
    else:
        bot.send_message(message.chat.id, I_DONT_KNOW)
        bot.register_next_step_handler(message, settings_handler_step2)


@test_cancel
def settings_handler_step_notif_time(message: Message):
    if m := re.fullmatch(TIME_RE, message.text):
        notif_time = datetime.time(int(m.group(1)), int(m.group(2)))
        user_dao.update_notif_time(message.from_user.id, notif_time)
        bot.reply_to(message, OKAY, reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.from_user.id, "Мне нужно время в формате чч:мм")
        bot.register_next_step_handler(message, settings_handler_step_notif_time)


@test_cancel
def settings_handler_step_notif_days(message: Message, step_type):
    if message.text.isdigit():
        if step_type == "first":
            user_dao.update_first_notif(message.from_user.id, int(message.text))
        else:
            user_dao.update_second_notif(message.from_user.id, int(message.text))
        bot.reply_to(message, OKAY, reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.from_user.id, "Мне нужно число!")
        bot.register_next_step_handler(message, settings_handler_step_notif_days, step_type=step_type)


@test_cancel
def settings_handler_step_notif(message: Message):
    if message.text == "Включить":
        user_dao.update_notif(message.from_user.id, True)
        bot.reply_to(message, OKAY, reply_markup=ReplyKeyboardRemove())
    elif message.text == "Выключить":
        user_dao.update_notif(message.from_user.id, False)
        bot.reply_to(message, OKAY, reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.from_user.id, I_DONT_KNOW)
        bot.register_next_step_handler(message, settings_handler_step_notif)


@test_cancel
def settings_handler_step_btn(message: Message):
    if message.text == "Включить":
        user_dao.update_btn(message.from_user.id, False)
        bot.reply_to(message, OKAY, reply_markup=ReplyKeyboardRemove())
    elif message.text == "Выключить":
        user_dao.update_btn(message.from_user.id, True)
        bot.reply_to(message, OKAY, reply_markup=ReplyKeyboardRemove())
    else:
        bot.send_message(message.from_user.id, I_DONT_KNOW)
        bot.register_next_step_handler(message, settings_handler_step_notif)


@bot.message_handler(commands=['users'], auth=True)
def users_handler(message: Message):
    msgs = [f"{user['name']}{login_to_str(user['login'], ' (', ')')}"
            for user in user_dao.get_all_users()]
    for msg in list_split(msgs, sep='\n'):
        antiflood(bot.send_message, message.chat.id, msg)
