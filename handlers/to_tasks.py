import re
from telebot.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telebot.util import antiflood
from telebot.formatting import escape_html

from bot_core import bot, test_cancel, send_message_to_user
from db import task_dao
from misc import date_to_str, days_left_notif, list_split, lookahead, first_int, CR, days_left, rus_day, TaskState, \
    login_to_str, MAX_CAPTION_LEN, KEYBOARD_ROW_WIDTH, SEP_LINE


# ======================================
# ============ Список задач ============
# ======================================
@bot.message_handler(commands=['tasks'], auth=True)
def task_list_handler(message: Message):
    task_list_handler_int(message)


def task_list_handler_int(message: Message):
    tasks = task_dao.get_user_tasks(message.from_user.id, state=[TaskState.ACTIVE, TaskState.CREATED], by_date=True)
    if not tasks:
        bot.send_message(message.chat.id, "Нет предстоящих задач!")
    else:
        msgs = ["<b><i>Предстоящие задачи</i></b>"] + \
               [escape_html(f"{TaskState.get_ico(TaskState(task['state']))} ({task['cuid']}) {task['caption']}\n"
                            f"\tдо: {date_to_str(task['end_date'])}{days_left_notif(task['end_date'], ' (', ')')}")
                for task in tasks]
        control_task(message, tasks, msgs, 'cur')


@bot.message_handler(commands=['all_my_tasks'], auth=True)
def all_my_task_list_handler(message: Message):
    all_my_task_list_handler_int(message)


def all_my_task_list_handler_int(message: Message):
    tasks = task_dao.get_user_tasks(message.from_user.id)
    if not tasks:
        bot.send_message(message.chat.id, "Нет задач!")
    else:
        msgs = ["<b><i>Все мои задачи</i></b>"] + \
               [escape_html(f"{TaskState.get_ico(TaskState(task['state']))} ({task['cuid']}) {task['caption']}\n"
                            f"\tдо: {date_to_str(task['end_date'])} "
                            f"{days_left_notif(task['end_date'], '(', ')') if TaskState(task['state']) == TaskState.ACTIVE else ''}")
                for task in tasks]
        control_task(message, tasks, msgs, 'all')


def control_task_keyboard(tasks):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("❌ Выход", "🔄 Обновить")
    buttons = []
    for task in tasks:
        button = f"{task['cuid']} - {task['caption']}"
        buttons.append(button if len(button) <= MAX_CAPTION_LEN else button[:MAX_CAPTION_LEN - 3] + "...")
    # buttons = sorted(buttons, key=lambda s: first_int(s))
    if len(buttons) % 2 != 0:
        buttons.append('ㅤ')
    keyboard.add(*buttons, row_width=KEYBOARD_ROW_WIDTH)
    return keyboard


def control_task(message: Message, tasks, msgs, from_task):
    for msg, last in lookahead(list_split(msgs, sep=SEP_LINE)):
        if not last:
            antiflood(bot.send_message, message.chat.id, msg, parse_mode='HTML')
        else:
            antiflood(bot.send_message, message.chat.id, msg, parse_mode='HTML',
                      reply_markup=control_task_keyboard(tasks))
            bot.register_next_step_handler(message, task_select_handler, from_task)


def task_message(task, cur_user, deleted: bool = False):
    days = days_left(task['end_date'])
    days = f" осталось {days} {rus_day(days)}" if days != '-' else ''

    task_from = f"Задача от {task['from_user_name']}{login_to_str(task['from_user_login'], ' ')}\n" \
        if task['from_user'] != cur_user else ''

    state_ico = f"{TaskState.get_ico(TaskState(task['state']))}" if not deleted else TaskState.get_ico(TaskState.DELETE)

    msg = f"{state_ico} {task['caption']}\n" \
          f"{days_left_notif(task['end_date'], CR, CR)}" \
          f"\n" \
          f"Описание:\n" \
          f"{task['content']}\n" \
          f"\n" \
          f"Выполнить до: {date_to_str(task['end_date'])}{days} \n" \
          f"\n" \
          f"{task_from}" \
          f"Создана {task['create_date']}\n" \
          f"id: {task['cuid']}"
    return msg


def task_keyboard(task, from_task, cf_del: bool = False):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(TaskState.get_btn(TaskState.ACTIVE, task['small_btn']),
                             callback_data=f"mt_{TaskState.ACTIVE.value}_{task['cuid']}_{from_task}"),
        InlineKeyboardButton(TaskState.get_btn(TaskState.DONE, task['small_btn']),
                             callback_data=f"mt_{TaskState.DONE.value}_{task['cuid']}_{from_task}"),
        InlineKeyboardButton(TaskState.get_btn(TaskState.CANCEL, task['small_btn']),
                             callback_data=f"mt_{TaskState.CANCEL.value}_{task['cuid']}_{from_task}"))
    if cf_del:
        keyboard.add(InlineKeyboardButton(f'{TaskState.get_ico(TaskState.DELETE)} Да',
                                          callback_data=f"mt_det_{task['cuid']}_{from_task}"),
                     InlineKeyboardButton(f'{TaskState.get_ico(TaskState.DELETE)} Нет',
                                          callback_data=f"mt_def_{task['cuid']}_{from_task}"))
    else:
        keyboard.add(InlineKeyboardButton(f'{TaskState.get_btn(TaskState.DELETE, task["small_btn"])}',
                                          callback_data=f"mt_de_{task['cuid']}_{from_task}"))
    return keyboard


@test_cancel
def task_select_handler(message: Message, from_task):
    if message.text == '🔄 Обновить':
        if from_task == 'cur':
            task_list_handler_int(message)
        else:
            all_my_task_list_handler_int(message)
        return

    task = task_dao.get_user_task(message.from_user.id, first_int(message.text))
    if not task:
        bot.send_message(message.chat.id, "Задача не найдена")
    else:
        bot.send_message(message.chat.id, task_message(task, message.from_user.id),
                         reply_markup=task_keyboard(task, from_task))
    bot.register_next_step_handler(message, task_select_handler, from_task)


@bot.callback_query_handler(func=lambda call: str(call.data).startswith('mt'))
def edit_task_callback(call: CallbackQuery):
    m = re.match(r'mt_(\w+)_(\d+)_(\w+)', call.data)
    command = m.group(1)
    cuid = m.group(2)
    from_task = m.group(3)
    task = task_dao.get_user_task(call.from_user.id, cuid)
    if command == 'de':
        bot.answer_callback_query(call.id, "Подтверди удаление задачи, это необратимо.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                      reply_markup=task_keyboard(task, from_task, True))
    elif command == 'def':
        bot.answer_callback_query(call.id, "Ок")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                      reply_markup=task_keyboard(task, from_task))
    elif command == 'det':
        bot.answer_callback_query(call.id, "Задача удалена.")
        bot.edit_message_text(task_message(task, call.from_user.id, True), call.message.chat.id, call.message.id,
                              reply_markup=None)
        task_dao.delete(task['uid'])
        notif_author(task, TaskState(TaskState.DELETE))
    elif task['state'] != command:
        task['state'] = command
        task_dao.set_state(task['uid'], TaskState(command))
        bot.edit_message_text(task_message(task, call.from_user.id), call.message.chat.id, call.message.id,
                              reply_markup=task_keyboard(task, from_task))
        bot.answer_callback_query(call.id, f"Статус задачи изменен на  {TaskState.get_text(TaskState(command))}")
        notif_author(task, TaskState(command))
    else:
        bot.answer_callback_query(call.id, f"Статус задачи уже {TaskState.get_text(TaskState(command))}")


def notif_author(task, state: TaskState):
    if task['from_user'] != task['to_user']:
        msg = f"🔔\n" \
              f"Задача '{task['caption']}'\n" \
              f"назначенная тобой на {task['to_user_name']}{login_to_str(task['to_user_login'], ' (', ')')}\n" \
              f"сменила статус на: {TaskState.get_text(state)}"
        send_message_to_user(task['from_user'], msg, True)
