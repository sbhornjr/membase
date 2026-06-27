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
        self.last_op = {}

    def set(self, key, value, namespace, track_history=True):
        self.last_op[namespace] = (key, self.get(key, namespace))
        if namespace not in self.db:
            self.db[namespace] = {}
        self.db[namespace][key] = value
        if namespace not in self.db_counts:
            self.db_counts[namespace] = {}
        if value in self.db_counts[namespace]:
            self.db_counts[namespace][value] += 1
        else:
            self.db_counts[namespace][value] = 1
        if track_history and self.config.enable_history:
            self._track_history(key, value, namespace)

    def get(self, key, namespace):
        return self.db[namespace][key] if key in self.db.get(namespace, {}) else None

    def delete(self, key, namespace, track_history=True):
        self.last_op[namespace] = (key, self.get(key, namespace))
        if key in self.db.get(namespace, {}):
            value = self.db[namespace][key]
            del self.db[namespace][key]
            self.db_counts[namespace][value] -= 1
            if self.db_counts[namespace][value] == 0:
                del self.db_counts[namespace][value]
            if not self.db_counts[namespace]:
                del self.db_counts[namespace]
            if track_history and self.config.enable_history:
                self._track_history(key, None, namespace)

    def count(self, value, namespace):
        return self.db_counts[namespace][value] if value in self.db_counts.get(namespace, {}) else 0
    
    def get_keys(self, namespace):
        return list(self.db.get(namespace, {}).keys())
    
    def exists(self, key, namespace):
        return key in self.db.get(namespace, {})
    
    def find(self, value, namespace):
        return [key for key, val in self.db.get(namespace, {}).items() if val == value]
    
    def dump(self, namespace):
        print(json.dumps(self.db.get(namespace, {}), indent=4))

    def clear(self, namespace):
        if self.db.get(namespace, None):
            self.db[namespace].clear()
            self.db_counts[namespace].clear()
            if self.last_op.get(namespace, None):
                del self.last_op[namespace]
            if self.config.enable_history and self.db_history.get(namespace, None):
                self.db_history[namespace].clear()

    def get_history(self, key, namespace):
        return self.db_history.get(namespace, {}).get(key, None) if self.config.enable_history else None
    
    def extend_history(self, history, namespace):
        for key, history in history.items():
            if namespace not in self.db_history:
                self.db_history[namespace] = {}
            if key not in self.db_history[namespace]:
                self.db_history[namespace][key] = history
            else:
                self.db_history[namespace][key].extend(history)

    def get_size(self, namespace):
        return len(self.db.get(namespace, {}))
    
    def undo(self, namespace, track_history):
        if not self.last_op[namespace]:
            print("No operation to undo.")
            return
        key, value = self.last_op[namespace]
        if value:
            self.set(key, value, namespace, track_history)
        else:
            self.delete(key, namespace, track_history)
        self.last_op[namespace] = None

    def get_namespaces(self):
        return list(self.db.keys())

    def _track_history(self, key, value, namespace, timestamp=None):
        if namespace not in self.db_history:
            self.db_history[namespace] = {}
        self.db_history[namespace].setdefault(key, []).append((timestamp or datetime.now(ZoneInfo("America/New_York")).isoformat(), value))