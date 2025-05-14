from src.database import Database
from src.transaction_manager import TransactionManager
from src.persistence_manager import PersistenceManager
from src.stats import StatsTracker

def print_help():
    print("Available commands:")
    print("set <key> <value> - Set a key-value pair")
    print("get <key> - Get the value for a key")
    print("delete <key> - Delete a key-value pair")
    print("count <value> - Count occurrences of a value")
    print("begin - Start a transaction")
    print("commit - Commit the current transaction")
    print("rollback - Rollback the current transaction")
    print("exit - Exit the program")
    print("keys - List all keys")
    print("exists <key> - Check if a key exists")
    print("find <value> - Find keys with a specific value")
    print("dump - Dump the database")
    print("clear - Clear the database")
    print("snapshot - Create a snapshot of the current state")
    print("history <key> - Get the history of a key")
    print("help - Show this help message")

def main():
    stats = StatsTracker()
    db = Database()
    pm = PersistenceManager(db, stats)
    tm = TransactionManager(db, pm)
    db.startup()
    print("Welcome to membase, an in-memory Key-Value store!")
    while True:
        command = input(">> ").strip()
        if command == "exit":
            pm.close()
            break
        elif command.lower().startswith("set"):
            _, key, value = command.split()
            if tm.transactions_active > 0:
                tm.add_command(key, value)
            else:
                pm.add_command(command)
            db.set(key, value, tm.transactions_active == 0)
            stats.set_ops += 1
        elif command.lower().startswith("get"):
            _, key = command.split()
            value = db.get(key)
            if value is not None:
                print(f"{key} = {value}")
            else:
                print(f"{key} not found")
            stats.get_ops += 1
        elif command.lower().startswith("delete"):
            _, key = command.split()
            if tm.transactions_active > 0:
                tm.add_command(key)
            else:
                pm.add_command(command)
            db.delete(key, tm.transactions_active == 0)
            stats.delete_ops += 1
        elif command.lower().startswith("count"):
            _, value = command.split()
            count = db.count(value)
            print(f"Count of {value}: {count}")
        elif command.lower() == "begin":
            tm.begin()
        elif command.lower() == "commit":
            tm.commit()
            stats.commits += 1
        elif command.lower() == "rollback":
            tm.rollback()
            stats.rollbacks += 1
        elif command.lower() == "keys":
            print(db.get_keys())
        elif command.lower().startswith("exists"):
            _, key = command.split()
            exists = db.exists(key)
            print(str(exists))
        elif command.lower().startswith("find"):
            _, value = command.split()
            print(db.find(value))
        elif command.lower() == "dump":
            db.dump()
        elif command.lower() == "clear":
            db.clear()
            pm.clear()
            print("Database cleared")
        elif command.lower() == "snapshot":
            pm.snapshot()
            print("Snapshot created")
        elif command.lower().startswith("history"):
            _, key = command.split()
            print(db.get_history(key))
        elif command.lower() == "size":
            print(db.get_size())
        elif command.lower() == "stats":
            print(stats.get_stats())
        elif command.lower() == "undo":
            db.undo()
        elif command.lower() == "help":
            print_help()
        else:
            print("Unknown command. Available commands: set, get, delete, count, begin, commit, rollback, exit")
        
        

if __name__ == "__main__":
    main()