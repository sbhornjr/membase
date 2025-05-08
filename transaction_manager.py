class TransactionManager():
    def __init__(self, db):
        self.db = db
        self.transactions_stack = []
        self.transactions_active = 0

    def begin(self):
        self.transactions_active += 1
        self.transactions_stack.append([])

    def commit(self):
        if self.transactions_active == 0:
            print("transaction not started")
            return
        self.transactions_active -= 1
        committed = self.transactions_stack.pop()
        if self.transactions_active == 0:
            return
        for command in committed:
            if command[0] not in list(map(lambda x: x[0], self.transactions_stack[-1])):
                self.transactions_stack[-1].append(command)

    def rollback(self):
        if self.transactions_active == 0:
            print("transaction not started")
            return
        self.transactions_active -= 1
        rolled_back = self.transactions_stack.pop()
        for command in rolled_back:
            self._undo(command)

    def _undo(self, command):
        key, value = command[0], command[1]
        if value:
            self.db.set(key, value)
        else:
            self.db.delete(key)
            