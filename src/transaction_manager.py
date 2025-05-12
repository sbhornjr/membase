from src.persistence_manager import PersistenceManager

class TransactionManager():
    def __init__(self, db, pm):
        self.db = db
        self.transactions_stack = []
        self.transactions_active = 0
        self.persistence_manager = pm

    def begin(self):
        self.transactions_active += 1
        self.transactions_stack.append({})

    def commit(self):
        if self.transactions_active == 0 or not self.transactions_stack:
            print("transaction not started")
            return
        self.transactions_active -= 1
        committed = self.transactions_stack.pop()
        if self.transactions_active == 0:
            self.persistence_manager.add_commands(self._setup_commands_for_log(committed))
        else:
            for key, value in committed.items():
                if key not in self.transactions_stack[-1]:
                    self.transactions_stack[-1][key] = value

    def rollback(self):
        if self.transactions_active == 0 or not self.transactions_stack:
            print("transaction not started")
            return
        self.transactions_active -= 1
        rolled_back = self.transactions_stack.pop()
        for key, value in rolled_back.items():
            self._undo(key, value)

    def add_command(self, key):
        if self.transactions_active == 0 or not self.transactions_stack:
            print("transaction not started")
            return
        self.transactions_stack[-1][key] = self.db.get(key)

    def _undo(self, key, value):
        if value:
            self.db.set(key, value)
        else:
            self.db.delete(key)

    def _setup_commands_for_log(self, commands):
        log_commands = []
        for command in commands:
            # if the key is in the db, that means we stored the old value in case of rollback, whether the value is None (new key) or not, and set the key to the new value
            if self.db.get(command):
                log_commands.append(f"set {command} {self.db.get(command)}")
            # if the key is not in the db, that means we stored the old value in case of rollback, and we deleted the key
            else:
                log_commands.append(f"delete {command}")
        return log_commands

            