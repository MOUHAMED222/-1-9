import sqlite3
import logging
from contextlib import contextmanager
from config import DATABASE_NAME

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path=DATABASE_NAME):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    language TEXT DEFAULT 'ar'
                )
            ''')
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    maintenance_mode INTEGER DEFAULT 0,
                    ban_list TEXT DEFAULT ''
                )
            ''')
            # Ensure settings row exists
            cursor.execute('INSERT OR IGNORE INTO settings (id, maintenance_mode, ban_list) VALUES (1, 0, "")')
            conn.commit()
        logger.info("Database initialized")

    # User operations
    def add_user(self, user_id, username, first_name, last_name, language='ar'):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, language)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, language))
            conn.commit()

    def get_user_lang(self, user_id):
        with self.get_connection() as conn:
            row = conn.execute('SELECT language FROM users WHERE user_id = ?', (user_id,)).fetchone()
            return row['language'] if row else None

    def set_user_lang(self, user_id, lang):
        with self.get_connection() as conn:
            conn.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
            conn.commit()

    def get_all_users(self):
        with self.get_connection() as conn:
            return [row['user_id'] for row in conn.execute('SELECT user_id FROM users')]

    def count_users(self):
        with self.get_connection() as conn:
            return conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]

    # Settings operations
    def get_settings(self):
        with self.get_connection() as conn:
            row = conn.execute('SELECT maintenance_mode, ban_list FROM settings WHERE id = 1').fetchone()
            return dict(row)

    def set_maintenance(self, mode: bool):
        with self.get_connection() as conn:
            conn.execute('UPDATE settings SET maintenance_mode = ? WHERE id = 1', (1 if mode else 0,))
            conn.commit()

    def get_ban_list(self):
        with self.get_connection() as conn:
            ban_str = conn.execute('SELECT ban_list FROM settings WHERE id = 1').fetchone()[0]
            return [int(x) for x in ban_str.split(',') if x.strip()]

    def add_to_ban_list(self, user_id):
        with self.get_connection() as conn:
            current = conn.execute('SELECT ban_list FROM settings WHERE id = 1').fetchone()[0]
            ban_list = [x for x in current.split(',') if x] + [str(user_id)]
            conn.execute('UPDATE settings SET ban_list = ? WHERE id = 1', (','.join(ban_list),))
            conn.commit()

    def remove_from_ban_list(self, user_id):
        with self.get_connection() as conn:
            current = conn.execute('SELECT ban_list FROM settings WHERE id = 1').fetchone()[0]
            ban_list = [x for x in current.split(',') if x and int(x) != user_id]
            conn.execute('UPDATE settings SET ban_list = ? WHERE id = 1', (','.join(ban_list),))
            conn.commit()

    def is_banned(self, user_id):
        return user_id in self.get_ban_list()

db = Database()