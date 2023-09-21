
import pickle

from telebot.handler_backends import HandlerBackend


class PgHandlerBackend(HandlerBackend):

    def __init__(self, dao, handlers=None):
        super().__init__(handlers)
        self.dao = dao

    @staticmethod
    def _key(handle_group_id):
        return str(handle_group_id)

    def register_handler(self, handler_group_id, handler):
        handlers = []
        value = self.dao.get(self._key(handler_group_id))
        if value:
            handlers = pickle.loads(value)
        handlers.append(handler)
        self.dao.set(self._key(handler_group_id), pickle.dumps(handlers))

    def clear_handlers(self, handler_group_id):
        self.dao.delete(self._key(handler_group_id))

    def get_handlers(self, handler_group_id):
        handlers = None
        value = self.dao.get(self._key(handler_group_id))
        if value:
            handlers = pickle.loads(value)
            self.clear_handlers(handler_group_id)
        return handlers
