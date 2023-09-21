from schedule import repeat, every, CancelJob
from bot_core import send_message_to_user

from db import task_dao
from misc import time_to_str, days_delta_to_ico, rus_day, date_to_str

planed_notifications = []


def send_notification(notif):
    try:
        if notif['days_to'] > 0:
            date_str = f"через {notif['days_to']} {rus_day(notif['days_to'])} ({date_to_str(notif['end_date'])})"
        else:
            date_str = "сегодня"
        msg = f"🔔\n" \
              f"{days_delta_to_ico(notif['days_to'])} Напоминаю, что срок выполнения задачи '{notif['caption']}' " \
              f"истекает {date_str}"
        send_message_to_user(notif['to_user'], msg, True)
    finally:
        planed_notifications.remove(notif['uid'])
        return CancelJob


@repeat(every(5).minutes)
def search_notification():
    try:
        for notif in task_dao.get_task_to_notif():
            if notif['uid'] not in planed_notifications:
                planed_notifications.append(notif['uid'])
                every().day.at(time_to_str(notif['notif_time'])).do(send_notification, notif)
    except Exception as e:
        print(e)
