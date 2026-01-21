"""
Central Database Manager using TinyDB.
Handles persistence for price history, user settings, and active sessions in a single NoSQL store.
"""
from tinydb import TinyDB, Query
from pathlib import Path

DB_PATH = Path("smart_deal_db.json")

class DatabaseManager:
    def __init__(self):
        self._db = TinyDB(DB_PATH)
        self.history = self._db.table('history')
        self.users = self._db.table('users')
        self.session = self._db.table('session')
        self.query = Query()

    def get_db(self):
        return self._db
        
    def close(self):
        self._db.close()

# Singleton instance
db = DatabaseManager()
