from enum import Enum


class TaskTo:
    def __init__(self, from_user_id, to_user_id):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.caption = None
        self.content = None
        self.end_date = None


class ListedEnum(Enum):
    @classmethod
    def list(cls) -> list:
        return list(map(lambda c: c.value, cls))

    @classmethod
    def qstr(cls) -> str:
        return ", ".join(["'" + e + "'" for e in cls.list()])


class TaskState(ListedEnum):
    CREATED = 'CREATED'
    ACTIVE = 'ACTIVE'
    DONE = 'DONE'
    CANCEL = 'CANCEL'
    DELETE = 'DELETE'

    @classmethod
    def get_ico(cls, state):
        if state == TaskState.CREATED:
            return '🆕'
        if state == TaskState.ACTIVE:
            return '📎'
        if state == TaskState.CANCEL:
            return '🚫'
        if state == TaskState.DONE:
            return '✅'
        if state == TaskState.DELETE:
            return '🗑'
        return None

    @classmethod
    def get_btn(cls, state, small_btn=False):
        if state == TaskState.ACTIVE:
            return f'{cls.get_ico(state)}{"" if small_btn else " в работу"}'
        if state == TaskState.CANCEL:
            return f'{cls.get_ico(state)}{"" if small_btn else " отменить"}'
        if state == TaskState.DONE:
            return f'{cls.get_ico(state)}{"" if small_btn else " сделано"}'
        if state == TaskState.DELETE:
            return f'{cls.get_ico(state)}{"" if small_btn else " удалить"}'
        return None

    @classmethod
    def get_desk(cls, state):
        if state == TaskState.CREATED:
            return 'создана'
        if state == TaskState.ACTIVE:
            return 'в работе'
        if state == TaskState.CANCEL:
            return 'отменена'
        if state == TaskState.DONE:
            return 'выполнена'
        if state == TaskState.DELETE:
            return 'удалена'
        return None

    @classmethod
    def get_text(cls, state):
        return f"{cls.get_ico(state)} ({cls.get_desk(state)})"
