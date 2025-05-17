from src.persistence_manager import PersistenceManager
from datetime import datetime
from zoneinfo import ZoneInfo

class TransactionManager():
    def __init__(self, db, pm):
        self.db = db
        self.transactions_stack = []
        self.history_stack = [] if db.config.enable_history else None
        self.transactions_active = 0
        self.persistence_manager = pm

    def begin(self):
        self.transactions_active += 1
        self.transactions_stack.append({})
        if self.history_stack is not None:
            self.history_stack.append({})

    def commit(self):
        if self.transactions_active == 0 or not self.transactions_stack:
            print("transaction not started")
            return
        self.transactions_active -= 1
        committed = self.transactions_stack.pop()
        if self.history_stack:
            self._commit_history()
        if self.transactions_active == 0:
            self.persistence_manager.add_commands(self._setup_commands_for_log(committed))
        else:
            for key, value in committed.items():
                if key in self.transactions_stack[-1]:
                    self.transactions_stack[-1][key].extend(value)
                else:
                    self.transactions_stack[-1][key] = value

    def rollback(self):
        if self.transactions_active == 0 or not self.transactions_stack:
            print("transaction not started")
            return
        self.transactions_active -= 1
        self.history_stack.pop()
        rolled_back = self.transactions_stack.pop()
        for key, value in rolled_back.items():
            self._undo(key, value)

    def add_command(self, key, value=None):
        if self.transactions_active == 0 or not self.transactions_stack:
            print("transaction not started")
            return
        self.transactions_stack[-1].setdefault(key, []).append(self.db.get(key))
        if self.history_stack:
            self.history_stack[-1].setdefault(key, []).append((datetime.now(ZoneInfo("America/New_York")).isoformat(), value))

    def rollback_all(self):
        while self.transactions_active > 0:
            self.rollback()

    def _undo(self, key, op_list):
        for value in op_list[::-1]:
            if value:
                self.db.set(key, value, False)
            else:
                self.db.delete(key, False)

    def _commit_history(self):
        committed_history = self.history_stack.pop()
        if self.transactions_active == 0:
            self.db.extend_history(committed_history)
        else:
            for key, history in committed_history.items():
                if key not in self.history_stack[-1]:
                    self.history_stack[-1][key] = history
                else:
                    self.history_stack[-1][key].extend(history)

    def _setup_commands_for_log(self, commands):
        log_commands = []
        for command in commands:
            for op in commands[command]:
                # if the key is in the db, that means we stored the old value in case of rollback, whether the value is None (new key) or not, and set the key to the new value
                if self.db.get(command):
                    log_commands.append(f"set {command} {self.db.get(command)}")
                # if the key is not in the db, that means we stored the old value in case of rollback, and we deleted the key
                else:
                    log_commands.append(f"delete {command}")
        return log_commands

            