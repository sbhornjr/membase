from database import Database
from transaction_manager import TransactionManager

def main():
    db = Database()
    tm = TransactionManager(db)
    while True:
        command = input(">> ").strip()
        if command == "exit":
            break
        elif command.lower().startswith("set"):
            _, key, value = command.split()
            if tm.transaction_active:
                tm.transaction_stack.append(("set", key, db.get(key)))
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
            if tm.transaction_active:
                tm.transaction_stack.append(("delete", key, db.get(key)))
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