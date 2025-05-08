class TransactionManager():
    def __init__(self, db):
        self.db = db
        self.transaction_stack = []
        self.transaction_active = False

    def begin(self):
        if self.transaction_active:
            print("transaction already started")
            return
        self.transaction_active = True

    def commit(self):
        if not self.transaction_active:
            print("transaction not started")
            return
        self.transaction_active = False
        self.transaction_stack = []

    def rollback(self):
        if not self.transaction_active:
            print("transaction not started")
            return
        while self.transaction_stack:
            self.undo(self.transaction_stack.pop())
        self.transaction_active = False

    def undo(self, command):
        if command[0] == "set":
            key, value = command[1], command[2]
            if value:
                self.db.set(key, value)
            else:
                self.db.delete(key)
        elif command[0] == "delete":
            key, value = command[1], command[2]
            self.db.set(key, value)
            