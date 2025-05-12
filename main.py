from src.database import Database
from src.transaction_manager import TransactionManager
from src.persistence_manager import PersistenceManager

def main():
    db = Database()
    pm = PersistenceManager(db)
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
                tm.add_command(key)
            else:
                pm.add_command(command)
            db.set(key, value)
        elif command.lower().startswith("get"):
            _, key = command.split()
            value = db.get(key)
            if value is not None:
                print(f"{key} = {value}")
            else:
                print(f"{key} not found")
        elif command.lower().startswith("delete"):
            _, key = command.split()
            if tm.transactions_active > 0:
                tm.add_command(key)
            else:
                pm.add_command(command)
            db.delete(key)
        elif command.lower().startswith("count"):
            _, value = command.split()
            count = db.count(value)
            print(f"Count of {value}: {count}")
        elif command.lower() == "begin":
            tm.begin()
        elif command.lower() == "commit":
            tm.commit()
        elif command.lower() == "rollback":
            tm.rollback()
        else:
            print("Unknown command. Available commands: set, get, delete, count, begin, commit, rollback, exit")
        
        

if __name__ == "__main__":
    main()