from telebot.formatting import escape_html
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telebot.util import antiflood, smart_split

from bot_core import bot, test_cancel
from db import task_dao
from misc import date_to_str, list_split, TaskState, login_to_str, SEP_LINE


# ========================================================
# ================== Список всех задач ===================
# ========================================================
@bot.message_handler(commands=['all_tasks'], auth=True)
def all_task_list_handler(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Только активные")
    keyboard.add("Вообще все")
    bot.send_message(message.chat.id, "Какие задачи будем смотреть?", reply_markup=keyboard)
    bot.register_next_step_handler(message, all_task_list_handler_step2)


@test_cancel
def all_task_list_handler_step2(message: Message):
    if message.text == 'Вообще все':
        tasks = task_dao.get_all_tasks()
        msgs = ["<b><i>Все задачи (включая не активные)</i></b>"]
    elif message.text == 'Только активные':
        tasks = task_dao.get_all_tasks(state=[TaskState.CREATED, TaskState.ACTIVE])
        msgs = ["<b><i>Все задачи</i></b>"]
    else:
        bot.send_message(message.chat.id, "Так какие задачи будем смотреть?")
        bot.register_next_step_handler(message, all_task_list_handler_step2)
        return

    def user_label(u_task):
        return escape_html(f"Назначенные на {u_task['to_user_name']}"
                           f"{login_to_str(u_task['to_user_login'], ' (', ')')}\n")

    if not tasks:
        bot.send_message(message.chat.id, "Вообще нет задач!")
    else:
        cur_usr = tasks[0]['to_user']
        msg = user_label(tasks[0])
        for task in tasks:
            if cur_usr != task['to_user']:
                msgs.append(msg)
                msg = user_label(task)
                cur_usr = task['to_user']
            msg += escape_html(f"\t\t\t\t{TaskState.get_ico(TaskState(task['state']))} \"{task['caption']}\" "
                               f"до: {date_to_str(task['end_date'])}\n")
        msgs.append(msg)

        for msg in list_split(msgs, sep=SEP_LINE):
            for msg_part in smart_split(msg):
                antiflood(bot.send_message, message.from_user.id, msg_part, parse_mode='HTML',
                          reply_markup=ReplyKeyboardRemove())
