class Database():
    def __init__(self):
        self.db = {}
        self.db_counts = {}

    def set(self, key, value):
        self.db[key] = value
        if value in self.db_counts:
            self.db_counts[value] += 1
        else:
            self.db_counts[value] = 1

    def get(self, key):
        return self.db[key] if key in self.db else None

    def delete(self, key):
        if key in self.db:
            value = self.db[key]
            del self.db[key]
            self.db_counts[value] -= 1
            if self.db_counts[value] == 0:
                del self.db_counts[value]

    def count(self, value):
        return self.db_counts[value] if value in self.db_counts else 0