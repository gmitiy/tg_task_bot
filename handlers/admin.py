from datetime import datetime

import schedule
from telebot.types import Message, BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat, \
    ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUser, ReplyKeyboardRemove
from telebot.util import antiflood

from bot_core import bot, test_cancel, send_message_to_user
from db import user_dao
from misc import list_split, login_to_str, SEP_LINE

start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ======================================
# ========== Отправка всем =============
# ======================================
@bot.message_handler(commands=['send_to_all'], send_to_all=True)
def send_to_all_handler(message: Message):
    bot.send_message(message.chat.id, "Пришли текст который я перешлю всем.")
    bot.register_next_step_handler(message, send_to_all_handler_step2)


@test_cancel
def send_to_all_handler_step2(message: Message):
    bot.send_message(message.chat.id, "Так будет выглядеть твое сообщение у других. Пришли 'Да' если можно отправлять!")
    bot.send_message(message.chat.id, message.text)
    bot.register_next_step_handler(message, send_to_all_handler_step3, msg=message.text)


@test_cancel
def send_to_all_handler_step3(message: Message, msg):
    if message.text.lower() == "да":
        for user_id in user_dao.get_all_users_id_except(message.from_user.id):
            send_message_to_user(user_id, msg)
        antiflood(bot.send_message, message.chat.id, "Все отправил.")
    else:
        bot.send_message(message.chat.id, "Ну нет, так нет.")


# ======================================
# ============== Админ =================
# ======================================
@bot.message_handler(commands=['update_commands'], admin=True)
def update_commands_handler(message: Message):
    default_commands = [
        BotCommand('tasks', 'Предстоящие задачи'),
        BotCommand('add', 'Поставить задачу'),
        BotCommand('from_tasks', 'Поставленные тобой задачи'),
        BotCommand('all_my_tasks', 'Все мои задачи'),
        BotCommand('all_from_tasks', 'Все поставленные тобой задачи'),
        BotCommand('all_tasks', 'Вообще все задачи'),
        BotCommand('delete_task', 'Удалить поставленную задачу'),
        BotCommand('settings', 'Настройки'),
        BotCommand('users', 'Список пользователей'),
        BotCommand('cancel', 'Прервать любую операцию'),
        BotCommand('dice', 'Кинуть кубик d6 ([/dice N] - кинуть N кубиков)')
    ]

    can_post_commands = [
        BotCommand('send_to_all', 'Отправить уведомление всем')
    ]

    admin_commands = [
        BotCommand('update_commands', 'Обновить меню'),
        BotCommand('set_can_post', 'Разрешить пользователю рассылать сообщения'),
        BotCommand('list_users', 'Список пользователей (adm)'),
        BotCommand('plan', 'Запланированные процессы')
    ]

    bot.set_my_commands(default_commands, BotCommandScopeAllPrivateChats())

    for user in user_dao.get_all_users():
        commands = default_commands.copy()
        if user['can_post']:
            commands += can_post_commands
        if user['is_admin']:
            commands += admin_commands
        if len(commands) != len(default_commands):
            antiflood(bot.set_my_commands, commands, BotCommandScopeChat(user['user_id']))

    bot.send_message(message.chat.id, "Готово.")


@bot.message_handler(commands=['set_can_post'], admin=True)
def set_can_post_handler(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Себе")
    keyboard.add(KeyboardButton("Выбрать контакт", request_user=KeyboardButtonRequestUser(1)))
    bot.send_message(message.chat.id, "Кому будем давать (отбирать) права?", reply_markup=keyboard)
    bot.register_next_step_handler(message, set_can_post_handler_step2)


@test_cancel
def set_can_post_handler_step2(message: Message):
    if message.text == "Себе":
        user_id = message.from_user.id
    elif message.content_type == 'user_shared':
        user_id = message.user_shared.user_id
    else:
        bot.send_message(message.chat.id, "Нужно выбрать пользователя!")
        bot.register_next_step_handler(message, set_can_post_handler_step2)
        return

    user = user_dao.get_user_info(user_id)
    if not user:
        bot.send_message(message.chat.id, "Я не знаком с этим человеком.", reply_markup=ReplyKeyboardRemove())
        return

    if user['can_post']:
        user_dao.update_can_post(user_id, False)
        bot.send_message(message.chat.id, f"Отобрал права у {user['name']}", reply_markup=ReplyKeyboardRemove())
    else:
        user_dao.update_can_post(user_id, True)
        bot.send_message(message.chat.id, f"Выдал права для {user['name']}", reply_markup=ReplyKeyboardRemove())

    bot.send_message(message.chat.id, "Не забудь обновить меню /update_commands", reply_markup=ReplyKeyboardRemove())


@bot.message_handler(commands=['list_users'], admin=True)
def list_users_handler(message: Message):
    msgs = [f"{login_to_str(user['login'], '[', '] - ')}{user['name']} "
            f"{'🔈' if user['notif_enable'] else '🔇'} "
            f"{'🖌' if user['can_post'] else ''} "
            f"{'⚙️' if user['is_admin'] else ''}"
            for user in user_dao.get_all_users()]
    for msg in list_split(msgs, sep='\n'):
        antiflood(bot.send_message, message.chat.id, msg)


@bot.message_handler(commands=['plan'], admin=True)
def plan_handler(message: Message):
    try:
        msgs = [f'Server time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\nBot start time: {start_time}'] + \
               [repr(job) for job in schedule.get_jobs()]
        for msg in list_split(msgs, sep=SEP_LINE):
            antiflood(bot.send_message, message.chat.id, msg)
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
