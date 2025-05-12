import json

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
    
    def startup(self):
        try:
            with open("data/snapshot.json", "r") as f:
                content = f.read()
                if not content.strip():
                    self.db = {}
                else:
                    self.db = json.loads(content)
                    for key, value in self.db.items():
                        if value in self.db_counts:
                            self.db_counts[value] += 1
                        else:
                            self.db_counts[value] = 1
        except FileNotFoundError:
            print("Error: Could not find snapshot file. Starting with an empty database.")
        except json.JSONDecodeError as e:
            print(f"Error: Corrupted snapshot file: {e}. Starting with an empty database.")
            self.db = {}
        except Exception as e:
            print(f"Unexpected error: {e}. Starting with an empty database.")
            self.db = {}
        try:
            with open("data/wal.log", "r") as f:
                for line in f:
                    command = line.strip()
                    if command.startswith("set"):
                        _, key, value = command.split()
                        self.set(key, value)
                    elif command.startswith("delete"):
                        _, key = command.split()
                        self.delete(key)
        except FileNotFoundError:
            pass