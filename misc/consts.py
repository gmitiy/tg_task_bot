import os


class EnvNotFoundException(Exception):
    pass


def get_env(name):
    if val := os.environ.get(name, None):
        return val
    raise EnvNotFoundException(f"Variable {name} not defined!")


CHAT_PASSWORD = get_env("CHAT_PASSWORD")
CHAT_PASSWORD_URL = get_env("CHAT_PASSWORD_URL")
BOT_KEY = get_env("BOT_KEY")
BOT_NAME = get_env("BOT_NAME")


class DB:
    URL = get_env("DB_URL")
    NAME = get_env("DB_NAME")
    SCHEMA = get_env("DB_SCHEMA")
    USER = get_env("DB_USER")
    PASS = get_env("DB_PASS")


CAN_DELETE_NOTIF = bool(os.environ.get("CAN_DELETE_NOTIF", False))

# noinspection SpellCheckingInspection
STICKERS_404 = [
    "CAACAgIAAxkBAAICHmQc3hqOZMH9fXtNJpCz5te98daJAAK8AQAC-IQHBJI_UGgDPONxLwQ",
    "CAACAgIAAxkBAAICH2Qc3iF2t3Xezzu8F0wjoXIqqb5UAALCAQAC-IQHBLtMM389c3M9LwQ",
    "CAACAgIAAxkBAAICIWQc3mJ4f4AbnCfA5oxYXkX_39x_AAJCAANN4DYGbHhZHNrydzkvBA",
    "CAACAgIAAxkBAAICI2Qc3ypZCW9v4WDMn1bAyL_FoN1gAAIzAAOP_v4KaWD71HCuRR4vBA",
    "CAACAgIAAxkBAAICJGQc32ZE4p2zPUF5VPJkoxDmVUI3AAJpEAAC6VUFGHE1bdbRrpenLwQ",
    "CAACAgIAAxkBAAICJWQc32uXcRGjc7SyOs1DPGjDFdmtAAIgAAMW8eoSoNZrSWtjQWAvBA",
    "CAACAgIAAxkBAAICJmQc334rM5elY5XcybZQVbScBMu-AAJWAAMjWc4M9eCRxWSU-0cvBA"
]

I_DONT_KNOW = "Я не понял. 😢"
OKAY = "Хорошо."
CR = '\n'
SEP_LINE = f'{CR}{"—" * 20}{CR}'

DATE_RE = r"(0?[1-9]|[12][0-9]|3[01])[\.,](0?[1-9]|1[012])[\.,]2\d{3}"
TIME_RE = r"([0-1][0-9]|2[0-3])[:-]([0-5][0-9])"
MAX_CAPTION_LEN = 22
KEYBOARD_ROW_WIDTH = 2
