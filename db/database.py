from contextlib import contextmanager
from datetime import date
from typing import ContextManager

from psycopg2 import pool
from psycopg2._psycopg import connection, cursor  # noqa
from psycopg2.extras import DictCursor, RealDictCursor

if __name__ == '__main__':
    import sys, os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from misc import DB, TaskTo, TaskState

db = pool.ThreadedConnectionPool(1, 10, host=DB.URL, database=DB.NAME, user=DB.USER,
                                 password=DB.PASS)


class CoreDAO:
    schema = DB.SCHEMA

    def __init__(self):
        self.schema = DB.SCHEMA
        self.table = None
        self.init_sql = None

    def init_table(self):
        if self.init_sql:
            with self.cursor() as cur:
                try:
                    cur.execute(self.init_sql)
                except Exception as e:
                    print(f"Can't create table {self.table}. Message: ", str(e))
                else:
                    print(f"Table {self.table} created.")
        else:
            print("Can't create table. No init SQL found")

    def drop_table(self):
        if self.table:
            with self.cursor() as cur:
                try:
                    cur.execute(f"DROP TABLE {self.table}")
                except Exception as e:
                    print(f"Can't drop table {self.table}. Message: ", str(e))
                else:
                    print(f"Table {self.table} drop.")
        else:
            print("Can't drop table. No table name found")

    @contextmanager
    def connection(self) -> ContextManager[connection]:
        _con = db.getconn()
        try:
            yield _con
        finally:
            db.putconn(_con)

    @contextmanager
    def cursor(self, cursor_factory: object = DictCursor) -> ContextManager[cursor]:
        with self.connection() as _conn:
            try:
                _cursor = _conn.cursor(cursor_factory=cursor_factory)
                try:
                    yield _cursor
                    _conn.commit()
                finally:
                    _cursor.close()
            except Exception as e:
                _conn.rollback()
                raise e


class HandlerBackendDAO(CoreDAO):
    key = 'handler'
    table = f"{CoreDAO.schema}.handle_backend"

    def __init__(self):
        super().__init__()
        self.table = HandlerBackendDAO.table
        self.init_sql = f"""
                    create table {self.table} (
                        handle_group_id text not null primary key,
                        handlers bytea,
                        update_at TIMESTAMPTZ NOT NULL DEFAULT NOW() 
                    )
                """

    def get(self, handle_group_id):
        with self.cursor() as cur:
            cur.execute(f"SELECT handlers FROM {self.table} WHERE handle_group_id = %s", (handle_group_id,))
            res = cur.fetchone()
            return res[0] if res else None

    def set(self, handle_group_id, handlers):
        with self.cursor() as cur:
            cur.execute(f"""INSERT INTO {self.table} (handle_group_id, handlers, update_at) 
                            VALUES (%(key)s, %(val)s, now()) 
                            ON CONFLICT (handle_group_id) DO UPDATE SET handlers = %(val)s, update_at = now()""",
                        {"key": handle_group_id, "val": handlers})

    def delete(self, handle_group_id):
        with self.cursor() as cur:
            cur.execute(f"DELETE FROM {self.table} WHERE handle_group_id = %s", (handle_group_id,))


class UserDAO(CoreDAO):
    key = 'user'
    table = f"{CoreDAO.schema}.user"

    def __init__(self):
        super().__init__()
        self.table = UserDAO.table
        self.init_sql = f"""
                    create table {self.table} (
                        user_id bigint NOT NULL PRIMARY KEY,
                        name text,
                        login text, 
                        notif_enable boolean NOT NULL DEFAULT true, 
                        first_notif_days integer NOT NULL DEFAULT 7,
                        second_notif_days integer NOT NULL DEFAULT 1,
                        notif_time TIME NOT NULL DEFAULT '12:00:00', 
                        small_btn boolean NOT NULL DEFAULT false, 
                        can_post boolean NOT NULL DEFAULT false, 
                        is_admin boolean NOT NULL DEFAULT false,
                        update_at TIMESTAMPTZ NOT NULL DEFAULT NOW() 
                    );
                """

    def add(self, user_id, name, login):
        with self.cursor() as cur:
            cur.execute(f"""
              INSERT INTO {self.table} (user_id, name, login) VALUES (%s, %s, %s) 
              ON CONFLICT (user_id) DO UPDATE SET update_at = now() 
            """, (user_id, name, login))

    def delete(self, user_id):
        with self.cursor() as cur:
            cur.execute(f"DELETE FROM {self.table} WHERE user_id = %s", (user_id,))

    def user_exists(self, user_id) -> bool:
        with self.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {self.table} WHERE user_id = %s", (user_id,))
            return bool(cur.fetchone())

    def get_user_info(self, user_id):
        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {self.table} WHERE user_id = %s", (user_id,))
            res = cur.fetchone()
            return res if res else None

    def get_all_users(self):
        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {self.table}")
            return cur.fetchall()

    def get_all_users_id_except(self, user_id):
        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT user_id FROM {self.table}  WHERE user_id != %s", (user_id,))
            # noinspection PyTypeChecker
            return (user['user_id'] for user in cur.fetchall())

    def update_notif_time(self, user_id, time):
        with self.cursor() as cur:
            cur.execute(f"UPDATE {self.table} SET notif_time = %s, update_at = now() WHERE user_id = %s",
                        (time, user_id,))

    def update_first_notif(self, user_id, days):
        with self.cursor() as cur:
            cur.execute(f"UPDATE {self.table} SET first_notif_days = %s, update_at = now() WHERE user_id = %s",
                        (days, user_id,))

    def update_second_notif(self, user_id, days):
        with self.cursor() as cur:
            cur.execute(f"UPDATE {self.table} SET second_notif_days = %s, update_at = now() WHERE user_id = %s",
                        (days, user_id,))

    def update_notif(self, user_id, enable: bool):
        with self.cursor() as cur:
            cur.execute(f"UPDATE {self.table} SET notif_enable = %s, update_at = now() WHERE user_id = %s",
                        (enable, user_id,))

    def update_btn(self, user_id, enable: bool):
        with self.cursor() as cur:
            cur.execute(f"UPDATE {self.table} SET small_btn = %s, update_at = now() WHERE user_id = %s",
                        (enable, user_id,))

    def update_can_post(self, user_id, can_post: bool):
        with self.cursor() as cur:
            cur.execute(f"UPDATE {self.table} SET can_post = %s, update_at = now() WHERE user_id = %s",
                        (can_post, user_id,))


class TaskDAO(CoreDAO):
    key = 'task'
    table = f"{CoreDAO.schema}.task"

    def __init__(self):
        super().__init__()
        self.table = TaskDAO.table
        self.init_sql = f"""
                    create table {self.table} (
                        uid serial PRIMARY KEY,
                        cuid integer NOT NULL,
                        to_user bigint NOT NULL,
                        from_user bigint NOT NULL,
                        create_date date NOT NULL DEFAULT NOW(),
                        end_date date,
                        state text NOT NULL DEFAULT 'CREATED' CHECK (state IN ({TaskState.qstr()})),
                        caption text NOT NULL, 
                        content text NOT NULL, 
                        update_at timestamptz NOT NULL DEFAULT NOW(),
                        UNIQUE (cuid, to_user)
                    )
                """

    def add(self, from_user_id, to_user_id, caption, content, end_date: date = None):
        with self.cursor() as cur:
            cur.execute(
                f"INSERT INTO {self.table} (cuid, from_user, to_user, end_date, caption, content) "
                f"SELECT coalesce(max(cuid)+1, 1), %s, %s, %s, %s, %s "
                f"  FROM {self.table} WHERE to_user = %s",
                (from_user_id, to_user_id, end_date, caption, content, to_user_id))

    def add_task(self, task: TaskTo):
        self.add(task.from_user_id, task.to_user_id, task.caption, task.content, task.end_date)

    def delete(self, uid):
        with self.cursor() as cur:
            cur.execute(f"DELETE FROM {self.table} WHERE uid = %s", (uid,))

    def set_state(self, uid, state: TaskState):
        with self.cursor() as cur:
            cur.execute(f"UPDATE {self.table} SET state = %s WHERE uid = %s", (state.value, uid))

    def get_state(self, uid) -> TaskState:
        with self.cursor() as cur:
            cur.execute(f"SELECT state FROM {self.table} WHERE uid = %s", (uid,))
            res = cur.fetchone()
            return TaskState(res[0]) if res else None

    def get_user_task(self, user_id, cuid):
        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT t.uid, t.cuid, t.from_user, u.name as from_user_name, u.login as from_user_login, "
                        f"       t.create_date, t.end_date, t.state, t.caption, t.content, "
                        f"       t.to_user, uu.name as to_user_name, uu.login as to_user_login, uu.small_btn "
                        f"FROM {self.table} t "
                        f"LEFT JOIN {UserDAO.table} u ON (t.from_user = u.user_id) "
                        f"LEFT JOIN {UserDAO.table} uu ON (t.to_user = uu.user_id) "
                        f"WHERE t.cuid = %s AND t.to_user = %s ", (cuid, user_id,))
            res = cur.fetchone()
            return res if res else None

    def get_task(self, uid):
        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT t.uid, t.cuid, t.from_user, u.name as from_user_name, u.login as from_user_login, "
                        f"       t.create_date, t.end_date, t.state, t.caption, t.content, "
                        f"       t.to_user, uu.name as to_user_name, uu.login as to_user_login, uu.small_btn "
                        f"FROM {self.table} t "
                        f"LEFT JOIN {UserDAO.table} u ON (t.from_user = u.user_id) "
                        f"LEFT JOIN {UserDAO.table} uu ON (t.to_user = uu.user_id) "
                        f"WHERE t.uid = %s", (uid,))
            res = cur.fetchone()
            return res if res else None

    def get_user_tasks_raw(self, user_id):
        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {self.table} WHERE to_user = %s", (user_id,))
            return cur.fetchall()

    def get_user_tasks_count(self, user_id):
        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT count(*) as cnt FROM {self.table} WHERE to_user = %s", (user_id,))
            res = cur.fetchone()
            # noinspection PyTypeChecker
            return res['cnt'] if res else 0

    def get_user_tasks(self, user_id, state: list[TaskState] = None, actual: bool = False, by_date: bool = False):
        state_exp = ''
        if state is not None:
            state_exp = "AND t.state IN ("
            for s in state:
                state_exp += f"'{s.value}', "
            state_exp = state_exp[:-2]
            state_exp += ") "

        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT t.uid, t.cuid, t.from_user, u.name as from_user_name, u.login as from_user_login, "
                        f"       t.create_date, t.end_date, t.state, t.caption, t.content, t.to_user "
                        f"FROM {self.table} t "
                        f"LEFT JOIN {UserDAO.table} u ON (t.from_user = u.user_id) "
                        f"WHERE t.to_user = %s "
                        f"{state_exp}"
                        f"""{"AND (t.end_date >= now() - INTERVAL '1 DAY' OR t.end_date IS NULL)" if actual else ''}"""
                        f"ORDER BY {'t.end_date' if by_date else 't.cuid'}", (user_id,))
            return cur.fetchall()

    def get_from_user_tasks(self, user_id, to_user=None, state: list[TaskState] = None, actual: bool = False,
                            by_date: bool = False, except_my: bool = False):
        state_exp = ''
        if state is not None:
            state_exp = "AND t.state IN ("
            for s in state:
                state_exp += f"'{s.value}', "
            state_exp = state_exp[:-2]
            state_exp += ") "

        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT t.uid, t.cuid, t.to_user, u.name as to_user_name, u.login as to_user_login, "
                        f"       t.create_date, t.end_date, t.state, t.caption, t.content "
                        f"FROM {self.table} t "
                        f"LEFT JOIN {UserDAO.table} u ON (t.to_user = u.user_id) "
                        f"WHERE t.from_user = %s "
                        f"{'AND t.to_user != t.from_user ' if except_my else ''}"
                        f"{'AND t.to_user = %s ' if to_user else ''}"
                        f"{state_exp}"
                        f"""{"AND (t.end_date >= now() - INTERVAL '1 DAY' OR t.end_date IS NULL) " if actual else ''}"""
                        f"ORDER BY {'t.end_date' if by_date else 't.cuid'}",
                        (user_id, to_user) if to_user else (user_id,))
            return cur.fetchall()

    def get_all_tasks(self, state: list[TaskState] = None, actual: bool = False):
        state_exp = ''
        if state is not None:
            state_exp = "AND t.state IN ("
            for s in state:
                state_exp += f"'{s.value}', "
            state_exp = state_exp[:-2]
            state_exp += ") "

        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT t.uid, t.cuid, "
                        f"       t.to_user, u.name as to_user_name, u.login as to_user_login, "
                        f"       t.from_user, uu.name as from_user_name, uu.login as from_user_login,"
                        f"       t.create_date, t.end_date, t.state, t.caption, t.content "
                        f"FROM {self.table} t "
                        f"LEFT JOIN {UserDAO.table} u ON (t.to_user = u.user_id) "
                        f"LEFT JOIN {UserDAO.table} uu ON (t.from_user = uu.user_id) "
                        f"WHERE 1 = 1 "
                        f"{state_exp}"
                        f"""{"AND (t.end_date >= now() - INTERVAL '1 DAY' OR t.end_date IS NULL) " if actual else ''}"""
                        f"ORDER BY t.to_user, t.end_date")
            return cur.fetchall()

    def get_task_to_notif(self):
        with self.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT t.to_user, t.state , t.caption, uu.notif_time, t.end_date, "
                        f"       t.end_date - current_date as days_to, t.uid "
                        f"FROM {self.table} t "
                        f"  LEFT OUTER JOIN {UserDAO.table} uu ON (t.to_user = uu.user_id) "
                        f"WHERE uu.notif_enable = TRUE "
                        f"  AND t.state IN ('{TaskState.CREATED.value}', '{TaskState.ACTIVE.value}') "
                        f"  AND (t.end_date = current_date + INTERVAL '1 day' * uu.first_notif_days "
                        f"    OR t.end_date = current_date + INTERVAL '1 day' * uu.second_notif_days "
                        f"    OR t.end_date = current_date) "
                        f" AND uu.notif_time BETWEEN (now() + INTERVAL '5 min')::time "
                        f"                       AND (now() + INTERVAL '15 min')::time ")
            return cur.fetchall()


_all_dao = [HandlerBackendDAO, UserDAO, TaskDAO]

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-l", "--list", help="List table keys",
                        required=False, action='store_true')
    parser.add_argument("-d", "--drop", help="Drop table by key [all]",
                        required=False, action="extend", nargs="+", type=str, metavar='dao_key')
    parser.add_argument("-u", "--update", help="Create table by key [all]",
                        required=False, action="extend", nargs="+", type=str, metavar='dao_key')

    if not any(vars(parser.parse_args()).values()):
        parser.error('No arguments provided.')

    args = parser.parse_args()
    if args.list:
        print(f"Table keys: {', '.join([dao.key for dao in _all_dao])}")
        exit()

    if args.drop:
        for dao in _all_dao:
            if ('all' in args.drop) or (dao.key in args.drop):
                dao().drop_table()

    if args.update:
        for dao in _all_dao:
            if ('all' in args.update) or (dao.key in args.update):
                dao().init_table()
