import json
from src.config import Config
from datetime import datetime
from zoneinfo import ZoneInfo

class Database():
    def __init__(self, config=None):
        self.config = config or Config()
        self.db = {}
        self.db_counts = {}
        self.db_history = {} if self.config.enable_history else None
        self.last_op = None

    def set(self, key, value, track_history=True):
        self.last_op = (key, self.get(key))
        self.db[key] = value
        if value in self.db_counts:
            self.db_counts[value] += 1
        else:
            self.db_counts[value] = 1
        if track_history and self.config.enable_history:
            self._track_history(key, value)

    def get(self, key):
        return self.db[key] if key in self.db else None

    def delete(self, key, track_history=True):
        self.last_op = (key, self.get(key))
        if key in self.db:
            value = self.db[key]
            del self.db[key]
            self.db_counts[value] -= 1
            if self.db_counts[value] == 0:
                del self.db_counts[value]
            if track_history and self.config.enable_history:
                self._track_history(key, None)

    def count(self, value):
        return self.db_counts[value] if value in self.db_counts else 0
    
    def get_keys(self):
        return list(self.db.keys())
    
    def exists(self, key):
        return key in self.db
    
    def find(self, value):
        return [key for key, val in self.db.items() if val == value]
    
    def dump(self):
        print(json.dumps(self.db, indent=4))

    def clear(self):
        self.db.clear()
        self.db_counts.clear()
        if self.config.enable_history:
            self.db_history.clear()

    def get_history(self, key):
        return self.db_history.get(key, None) if self.config.enable_history else None
    
    def extend_history(self, history):
        for key, history in history.items():
            if key not in self.db_history:
                self.db_history[key] = history
            else:
                self.db_history[key].extend(history)

    def get_size(self):
        return len(self.db)
    
    def undo(self):
        if not self.last_op:
            print("No operation to undo.")
            return
        key, value = self.last_op
        if value:
            self.set(key, value, False)
        else:
            self.delete(key, False)
        self.last_op = None

    def _track_history(self, key, value, timestamp=None):
        self.db_history.setdefault(key, []).append((timestamp or datetime.now(ZoneInfo("America/New_York")).isoformat(), value))