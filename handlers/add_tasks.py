import datetime
import re

from dateutil import parser
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUser, \
    ReplyKeyboardRemove

from bot_core import bot, test_cancel, call_admin, send_message_to_user
from db import task_dao, user_dao
from misc import date_to_str, CHAT_PASSWORD_URL, TaskTo, DATE_RE, BOT_NAME, TaskState


# ======================================
# ========== Добавление задачи =========
# ======================================
@bot.message_handler(commands=['add'], auth=True)
def task_add_handler(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Себе")
    keyboard.add(KeyboardButton("Выбрать контакт", request_user=KeyboardButtonRequestUser(1)))
    bot.send_message(message.chat.id, "Кому будем ставить задачу?", reply_markup=keyboard)
    bot.register_next_step_handler(message, task_add_handler_user)


@test_cancel
def task_add_handler_user(message: Message):
    if message.text == "Себе":
        user_id = message.from_user.id
    elif message.content_type == 'user_shared':
        user_id = message.user_shared.user_id
    else:
        bot.send_message(message.chat.id, "Нужно выбрать пользователя!")
        bot.register_next_step_handler(message, task_add_handler_user)
        return

    if not user_dao.user_exists(user_id):
        bot.send_message(message.chat.id, f"Я не знаком с этим человеком\\.\n"
                                          f"Пригласите его пообщаться со мной, чтобы ставить ему задачи\\.\n"
                                          f"[Ссылка приглашение](https://t.me/{BOT_NAME}?start={CHAT_PASSWORD_URL})",
                         parse_mode='MarkdownV2',
                         reply_markup=ReplyKeyboardRemove())
        return

    bot.send_message(message.chat.id, "Пришли заголовок задачи.", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, task_add_handler_caption, task_to=TaskTo(message.from_user.id, user_id))


@test_cancel
def task_add_handler_caption(message: Message, task_to: TaskTo):
    task_to.caption = message.text
    bot.send_message(message.chat.id, "Пришли полное описание задачи.")
    bot.register_next_step_handler(message, task_add_handler_content, task_to=task_to)


@test_cancel
def task_add_handler_content(message: Message, task_to: TaskTo):
    task_to.content = message.text
    bot.send_message(message.chat.id, "Пришли дату к которой надо выполнить задачу\\.\n"
                                      "Дата в формате __дд\\.мм\\.гггг__ \\(Пример: _01\\.05\\.2023_\\)\n"
                                      "Если у задачи нет даты окончания то пришли '\\-'",
                     parse_mode='MarkdownV2')
    bot.register_next_step_handler(message, task_add_handler_end_date, task_to=task_to)


@test_cancel
def task_add_handler_end_date(message: Message, task_to: TaskTo):
    if re.fullmatch(DATE_RE, message.text):
        try:
            task_to.end_date = parser.parse(message.text.replace(',', '.'), dayfirst=True)
        except Exception:
            call_admin(message.chat.id)
            return

    elif message.text != '-':
        bot.send_message(message.chat.id, "Нужна дата в формате __дд\\.мм\\.гггг__", parse_mode='MarkdownV2')
        bot.register_next_step_handler(message, task_add_handler_end_date, task_to=task_to)
        return

    if not task_to.end_date or task_to.end_date >= datetime.datetime.today():

        if task_dao.get_user_tasks_count(task_to.to_user_id) >= 200:
            if task_to.from_user_id == task_to.to_user_id:
                bot.send_message(message.chat.id, "У тебя уже 200 задач, больше поставить нельзя.\n"
                                                  "Удали завершенные задачи и повтори попытку.")
            else:
                bot.send_message(message.chat.id, "У пользователя уже 200 задач, больше поставить нельзя.\n"
                                                  "Попроси его удалить завершенные задачи и повтори попытку.")
                send_message_to_user(task_to.to_user_id,
                                     "🔔\n"
                                     "Тебе хотели поставить задачу, но не смогли так-как у тебя уже 200 задач.\n"
                                     "Пожалуйста удали завершенные задачи.")
            return

        msg = f"🔔\n" \
              f"{TaskState.get_ico(TaskState.CREATED)} Новая задача от {message.from_user.full_name}\n" \
              f"\n" \
              f"Заголовок: {task_to.caption}\n" \
              f"\n" \
              f"{task_to.content}\n" \
              f"\n" \
              f"Выполнить до: {date_to_str(task_to.end_date)}"

        if task_to.from_user_id == task_to.to_user_id or send_message_to_user(task_to.to_user_id, msg):
            task_dao.add_task(task_to)
            bot.send_message(message.chat.id, "Задача создана.")
        else:
            bot.send_message(message.chat.id, "Не удалось создать задачу.\n"
                                              "Возможно пользователь меня заблокировал.")
    else:
        bot.send_message(message.chat.id, "Нужно указать дату в будущем.")
        bot.register_next_step_handler(message, task_add_handler_end_date, task_to=task_to)
