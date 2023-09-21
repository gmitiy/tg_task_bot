from telebot.formatting import escape_html
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUser, \
    ReplyKeyboardRemove
from telebot.util import antiflood, extract_arguments

from bot_core import bot, test_cancel, send_message_to_user
from db import task_dao
from misc import date_to_str, days_left_notif, list_split, TaskState, login_to_str, SEP_LINE, OKAY


# ========================================================
# ============ Список назначенных тобой задач ============
# ========================================================
@bot.message_handler(commands=['all_from_tasks'], auth=True)
def all_from_task_list_handler(message: Message):
    tasks = task_dao.get_from_user_tasks(message.from_user.id, by_date=True, except_my=True)
    if not tasks:
        bot.send_message(message.chat.id, "Нет поставленных тобой задач!")
    else:
        msgs = ["<b><i>Задачи назначенные тобой на других пользователей</i></b>"] + \
               [escape_html(f"{TaskState.get_ico(TaskState(task['state']))} {task['caption']}\n"
                            f"\tназначена на {task['to_user_name']}{login_to_str(task['to_user_login'], ' (', ')')}\n"
                            f"\tдо: {date_to_str(task['end_date'])}{days_left_notif(task['end_date'], ' (', ')')}\n"
                            f"\tid: {task['uid']}")
                for task in tasks]
        for msg in list_split(msgs, sep=SEP_LINE):
            antiflood(bot.send_message, message.from_user.id, msg, parse_mode='HTML')


@bot.message_handler(commands=['from_tasks'], auth=True)
def from_task_list_handler(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Выбрать контакт", request_user=KeyboardButtonRequestUser(1)))
    bot.send_message(message.chat.id, "Задачи поставленные кому будем смотреть?", reply_markup=keyboard)
    bot.register_next_step_handler(message, from_task_list_handler_user)


@test_cancel
def from_task_list_handler_user(message: Message):
    if message.content_type == 'user_shared':
        tasks = task_dao.get_from_user_tasks(message.from_user.id, to_user=message.user_shared.user_id, by_date=True)
        if not tasks:
            bot.send_message(message.chat.id, "Нет поставленных тобой задач!", reply_markup=ReplyKeyboardRemove())
        else:
            msgs = [f"<b><i>Задачи назначенные тобой на "
                    f"{escape_html(tasks[0]['to_user_name'] + login_to_str(tasks[0]['to_user_login'], ' (', ')'))}"
                    f"</i></b>"] + \
                   [escape_html(f"{TaskState.get_ico(TaskState(task['state']))} {task['caption']}\n"
                                f"\tдо: {date_to_str(task['end_date'])}{days_left_notif(task['end_date'], ' (', ')')}\n"
                                f"\tid: {task['uid']}")
                    for task in tasks]
            for msg in list_split(msgs, sep=SEP_LINE):
                antiflood(bot.send_message, message.from_user.id, msg, reply_markup=ReplyKeyboardRemove(),
                          parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "Нужно выбрать пользователя!")
        bot.register_next_step_handler(message, from_task_list_handler_user)


@bot.message_handler(commands=['delete_task'], auth=True)
def delete_from_task_handler(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("❌ Отмена")
    bot.send_message(message.chat.id, "Пришли id задачи.", reply_markup=keyboard)
    bot.register_next_step_handler(message, delete_from_task_handler_s1)


@test_cancel
def delete_from_task_handler_s1(message: Message):
    uid = message.text
    if uid.isnumeric():
        task = task_dao.get_task(uid)
        if task is None:
            bot.send_message(message.chat.id, "Нет задачи с таким Id!")
            bot.register_next_step_handler(message, delete_from_task_handler_s1)
        elif task['from_user'] != message.from_user.id:
            bot.send_message(message.chat.id, "Задача с таким Id поставлена не тобой!",
                             reply_markup=ReplyKeyboardRemove())
        else:
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("Да", "Нет")
            bot.send_message(message.chat.id, f"Вы хотите удалить задачу:\n"
                                              f"{TaskState.get_ico(TaskState(task['state']))} {task['caption']}",
                             reply_markup=keyboard)
            bot.register_next_step_handler(message, delete_from_task_handler_s2, task)
    else:
        bot.send_message(message.chat.id, "Пришли id задачи (id можно узнать командами /from_tasks и /all_from_tasks)")
        bot.register_next_step_handler(message, delete_from_task_handler_s1)


@test_cancel
def delete_from_task_handler_s2(message: Message, task):
    if message.text == "Да":
        task_dao.delete(task["uid"])
        bot.send_message(message.chat.id, "Задача удалена.", reply_markup=ReplyKeyboardRemove())
        if task['from_user'] != task['to_user']:
            msg = f"🔔\n" \
                  f"Задача '{task['caption']}'\n" \
                  f"назначенная тебе: {task['from_user_name']}{login_to_str(task['from_user_login'], ' (', ')')}\n" \
                  f"была удалена автором."
            send_message_to_user(task['to_user'], msg, False)
    else:
        bot.send_message(message.chat.id, OKAY, reply_markup=ReplyKeyboardRemove())
