import re
from datetime import date

from .classes import *
from .consts import *


def login_to_str(login, lq='', rq=''):
    return f"{lq}@{login}{rq}" if login else ''


def first_int(value: str) -> int:
    if not value:
        return 0
    res = re.search(r'\d+', value)
    return int(res.group()) if res else 0


def lookahead(iterable):
    if iterable:
        it = iter(iterable)
        last = next(it)
        for val in it:
            yield last, False
            last = val
        yield last, True
    else:
        yield None, True


def rus_day(value):
    if value == '-' or value == '' or value is None:
        return ''
    value = int(value)
    words = ['день', 'дня', 'дней']
    if all((value % 10 == 1, value % 100 != 11)):
        return words[0]
    if all((2 <= value % 10 <= 4, any((value % 100 < 10, value % 100 >= 20)))):
        return words[1]
    return words[2]


def time_to_str(value):
    return value.strftime('%H:%M')


def date_to_str(value):
    if value and isinstance(value, date):
        return value.strftime('%d.%m.%Y')
    return "без срока"


def days_left(value) -> str:
    if value and isinstance(value, date):
        days = (value - date.today()).days
        return str(days) if days >= 0 else '-'
    return '-'


def days_delta_to_ico(days_delta):
    if days_delta < 0:
        return "‼️"
    if days_delta == 0:
        return "🔥"
    if days_delta <= 2:
        return "❗"
    if days_delta <= 7:
        return "⚠️"
    return ""


def days_left_notif(value, l_quote=None, r_quote=None):
    msg = None
    if value and isinstance(value, date):
        days_delta = (value - date.today()).days
        if days_delta < 0:
            msg = f"{days_delta_to_ico(days_delta)} просрочено"
        elif days_delta == 0:
            msg = f"{days_delta_to_ico(days_delta)} сегодня"
        elif days_delta <= 7:
            msg = f"{days_delta_to_ico(days_delta)} {days_delta} {rus_day(days_delta)}"
    if msg and (l_quote or r_quote):
        msg = f"{l_quote if l_quote else ''}{msg}{r_quote if r_quote else ''}"
    return msg if msg else ''


def list_split(data: list[str], sep: str = '\n') -> list[str]:
    res = []
    cur_msg = ''
    for msg, last in lookahead(data):
        if not last:
            if len(cur_msg) + len(msg) + len(sep) < 4000:
                cur_msg = cur_msg + msg + sep
            else:
                res.append(cur_msg)
                cur_msg = msg + sep
        else:
            if len(cur_msg) + len(msg) < 4000:
                res.append(cur_msg + msg)
            else:
                res.append(cur_msg)
                res.append(msg)
    return res
