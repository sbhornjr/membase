from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from src.database import Database
from src.persistence_manager import PersistenceManager
from src.transaction_manager import TransactionManager
from src.stats import Stats

# to run the server, use: os.system("uvicorn /absolute/path/to/server.main:app --host 127.0.0.1 --port 8000")

app = FastAPI()

db = Database()
stats = Stats()
pm = PersistenceManager(db, stats)
tm = TransactionManager(db, pm)

class KeyValue(BaseModel):
    key: str
    value: str

class Key(BaseModel):
    key: str

@app.post("/set")
def set_key(data: KeyValue):
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    if tm.transactions_active > 0:
        tm.add_command(data.key, data.value)
    else:
        pm.add_command(f"set {data.key} {data.value}")
    db.set(data.key, data.value, tm.transactions_active == 0)
    stats.set_ops += 1
    return {"message": f"Set {data.key} = {data.value}"}

@app.get("/get")
def get_key(key: str):
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    if key not in db.db:
        raise HTTPException(status_code=404, detail="Key not found")
    stats.get_ops += 1
    return {"value": db.get(key)}

@app.delete("/delete")
def delete_key(key: str):
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    if key in db.db:
        db.delete(key, tm.transactions_active == 0)
        stats.delete_ops += 1
        return {"message": f"Deleted {key}"}
    raise HTTPException(status_code=404, detail="Key not found")

@app.post("/begin")
def begin_transaction():
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    tm.begin()
    return {"message": "Transaction started"}

@app.post("/commit")
def commit_transaction():
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    if tm.transactions_active == 0 or not tm.transactions_stack:
        raise HTTPException(status_code=400, detail="No active transaction to commit")
    tm.commit()
    stats.commits += 1
    return {"message": "Transaction committed"}

@app.post("/rollback")
def rollback_transaction():
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    if tm.transactions_active == 0 or not tm.transactions_stack:
        raise HTTPException(status_code=400, detail="No active transaction to rollback")
    tm.rollback()
    stats.rollbacks += 1
    return {"message": "Transaction rolled back"}

@app.post("/namespace")
def switch_namespace(name: str):
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    tm.rollback_all()
    pm.snapshot()
    pm.namespace = name
    pm.startup()
    return {"message": f"Switched to namespace '{name}'"}

@app.get("/count")
def count_value(value: str):
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    count = db.count(value)
    return {"count": count}

@app.get("/keys")
def get_keys():
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    keys = db.get_keys()
    return {"keys": keys}

@app.get("/exists")
def check_exists(key: str):
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    exists = db.exists(key)
    return {"exists": exists}

@app.get("/find")
def find_value(value: str):
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    keys = db.find(value)
    return {"keys": keys}

@app.get("/dump")
def dump_database():
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    dump = db.dump()
    return {"db": dump}

@app.get("/clear")
def clear_database():
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    db.clear()
    pm.snapshot()
    return {"message": "Database cleared"}

@app.get("/snapshot")
def create_snapshot():
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    pm.snapshot()
    return {"message": "Snapshot created"}

@app.get("/stats")
def get_stats():
    return {
        "set_ops": stats.set_ops,
        "get_ops": stats.get_ops,
        "delete_ops": stats.delete_ops,
        "commits": stats.commits,
        "rollbacks": stats.rollbacks,
        "wal_size": stats.wal_size,
        "snapshot_size": stats.snapshot_size
    }

@app.get("/history")
def get_history(key: str):
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    history = db.get_history(key)
    if history is None:
        raise HTTPException(status_code=404, detail="No history found for this key")
    return {"history": history}

@app.get("/size")
def get_size():
    if not pm.namespace:
        raise HTTPException(status_code=400, detail="Namespace not set")
    size = db.size()
    return {"size": size}

@app.get("/")
def root():
    return {"message": "Welcome to the Key-Value Store API. Use /docs for API documentation."}


