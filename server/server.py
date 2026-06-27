from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from src.database import Database
from src.persistence_manager import PersistenceManager
from src.transaction_manager import TransactionManager
from src.stats import StatsTracker
from server.schemas import *
from server.error_codes import ErrorCode

# to run the server, use: os.system("uvicorn /absolute/path/to/server.main:app --host 127.0.0.1 --port 8000")

app = FastAPI()
db = Database()
stats = StatsTracker()
pm = PersistenceManager(db, stats)
tms = {}

for namespace in db.get_namespaces():
    tm = TransactionManager(db, pm, namespace)
    tms[namespace] = tm

class MembaseException(Exception):
    def __init__(self, *, status_code: int, code: str, message: str, recoverable: bool = True, suggested_action: str | None = None):
        self.status_code = status_code
        self.detail = ErrorDetail(
            code=code,
            message=message,
            recoverable=recoverable,
            suggested_action=suggested_action
        )
        super().__init__(message)

@app.exception_handler(MembaseException)
def handle_error(request, exc: MembaseException):
    response = ErrorResponse(error=exc.detail)
    response.ok = False

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )

@app.put("/v1/namespaces/{namespace}/keys/{key}", response_model=SetResponse, status_code=status.HTTP_201_CREATED)
def set_key(namespace: str, key: str, request: SetRequest):
    if not tms.get(namespace, None):
        tm = TransactionManager(db, pm, namespace)
        tms[namespace] = tm
    tm = tms.get(namespace)
    if tm.transactions_active > 0:
        tm.add_command(key, request.value)
    else:
        pm.add_command(f"set {key} {request.value}", namespace)
    old_value = db.get(key, namespace)
    db.set(key, request.value, namespace, tm.transactions_active == 0)
    stats.set_ops += 1
    response = SetResponse(
        ok=True,
        operation="set",
        namespace=namespace,
        key=key,
        value=request.value,
        old_value=old_value,
        transaction_depth=tm.transactions_active
    )
    return response

@app.get("/v1/namespaces/{namespace}/keys/{key}", response_model=GetResponse, status_code=status.HTTP_200_OK)
def get_key(namespace: str, key: str):
    if key not in db.db.get(namespace, {}):
        raise MembaseException(
            status_code=404,
            code=ErrorCode.KEY_NOT_FOUND,
            message=f"Key '{key}' not found in namespace '{namespace}'",
            recoverable=True,
            suggested_action="Use the /keys endpoint to see available keys or set the key using the /v1/namespaces/{namespace}/keys/{key} PUT endpoint."
        )
    stats.get_ops += 1
    response = GetResponse(
        ok=True,
        exists=True,
        namespace=namespace,
        key=key,
        value=db.get(key, namespace)
    )
    return response

@app.delete("/v1/namespaces/{namespace}/keys/{key}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
def delete_key(namespace: str, key: str):
    if key in db.db.get(namespace, {}):
        old_value = db.get(key, namespace)
        if not tms.get(namespace, None):
            tm = TransactionManager(db, pm, namespace)
            tms[namespace] = tm
        tm = tms.get(namespace)
        if tm.transactions_active > 0:
            tm.add_command(key)
        else:
            pm.add_command(f"delete {key}", namespace)
        db.delete(key, namespace, tm.transactions_active == 0)
        stats.delete_ops += 1
        new_value = db.get(key, namespace)
        response = DeleteResponse(
            ok=True,
            operation="delete",
            namespace=namespace,
            key=key,
            existed=True,
            old_value=old_value,
            value=new_value,
            transaction_depth=tm.transactions_active
        )
        return response
    raise MembaseException(
        status_code=404,
        code=ErrorCode.KEY_NOT_FOUND,
        message=f"Key '{key}' not found in namespace '{namespace}'",
        recoverable=True,
        suggested_action="Use the /keys endpoint to see available keys or set the key using the /v1/namespaces/{namespace}/keys/{key} PUT endpoint."
    )

@app.get("/v1/namespaces/{namespace}/transactions/begin", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
def begin_transaction(namespace: str):
    if not tms.get(namespace, None):
        tm = TransactionManager(db, pm, namespace)
        tms[namespace] = tm
    tm = tms.get(namespace)
    tm.begin()
    response = TransactionResponse(
        ok=True,
        operation="begin_transaction",
        transaction_depth=tm.transactions_active,
        namespace=namespace
    )
    return response

@app.get("/v1/namespaces/{namespace}/transactions/commit", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
def commit_transaction(namespace: str):
    if not tms.get(namespace, None):
            tm = TransactionManager(db, pm, namespace)
            tms[namespace] = tm
    tm = tms.get(namespace)
    if tm.transactions_active == 0 or not tm.transactions_stack:
        raise MembaseException(
            status_code=400,
            code=ErrorCode.NO_ACTIVE_TRANSACTION,
            message="No active transaction to commit",
            recoverable=True,
            suggested_action="Start a transaction using the /v/namespaces/{namespace}/transactions/begin endpoint before attempting to commit."
        )
    tm.commit()
    stats.commits += 1
    response = TransactionResponse(
        ok=True,
        operation="commit_transaction",
        transaction_depth=tm.transactions_active,
        namespace=namespace
    )
    return response

@app.get("/v1/namespaces/{namespace}/transactions/rollback", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
def rollback_transaction(namespace: str):
    if not tms.get(namespace, None):
            tm = TransactionManager(db, pm, namespace)
            tms[namespace] = tm
    tm = tms.get(namespace)
    if tm.transactions_active == 0 or not tm.transactions_stack:
        raise MembaseException(
            status_code=400,
            code=ErrorCode.NO_ACTIVE_TRANSACTION,
            message="No active transaction to rollback",
            recoverable=True,
            suggested_action="Start a transaction using the /v/namespaces/{namespace}/transactions/begin endpoint before attempting to rollback."
        )
    tm.rollback()
    stats.rollbacks += 1
    response = TransactionResponse(
        ok=True,
        operation="rollback_transaction",
        transaction_depth=tm.transactions_active,
        namespace=namespace
    )
    return response

@app.get("/v1/namespaces/{namespace}/clear", response_model=ClearResponse, status_code=status.HTTP_200_OK)
async def clear_namespace(namespace: str):
    db.clear(namespace)
    tm = tms.get(namespace, None)
    if tm:
        tm.rollback_all()
    await pm.snapshot(namespace)
    response = ClearResponse(
        ok=True,
        message="Namespace cleared",
        operation="clear_namespace"
    )

    return response

@app.post("/v1/namespaces/{namespace}/count", response_model=CountResponse, status_code=status.HTTP_200_OK)
def count_value(namespace: str, request: CountRequest):
    count = db.count(request.value, namespace)
    response = CountResponse(
        ok=True,
        value=request.value,
        count=count,
        namespace=namespace,
        operation="count_value"
    )
    return response

@app.get("/v1/namespaces/{namespace}/keys", response_model=GetKeysResponse, status_code=status.HTTP_200_OK)
def get_keys(namespace: str):
    keys = db.get_keys(namespace)
    response = GetKeysResponse(
        ok=True,
        keys=keys,
        namespace=namespace,
        operation="get_keys"
    )
    return response

@app.get("/v1/namespaces/{namespace}/keys/{key}/exists", response_model=ExistsResponse, status_code=status.HTTP_200_OK)
def check_exists(namespace: str, key: str):
    exists = db.exists(key, namespace)
    response = ExistsResponse(
        ok=True,
        exists=exists,
        key=key,
        namespace=namespace,
        operation="check_exists"
    )
    return response

@app.post("/v1/namespaces/{namespace}/find", response_model=FindResponse, status_code=status.HTTP_200_OK)
def find_value(namespace: str, request: FindRequest):
    keys = db.find(request.value, namespace)
    response = FindResponse(
        ok=True,
        keys=keys,
        namespace=namespace,
        operation="find_keys"
    )
    return response

@app.get("/v1/namespaces/{namespace}/dump", response_model=DumpResponse, status_code=status.HTTP_200_OK)
def dump_namespace(namespace: str):
    dump = db.db.get(namespace, {})
    response = DumpResponse(
        ok=True,
        data=dump,
        namespace=namespace,
        operation="dump_namespace"
    )
    return response

@app.get("/v1/namespaces/{namespace}/snapshot", response_model=SnapshotResponse, status_code=status.HTTP_200_OK)
async def create_snapshot(namespace: str):
    await pm.snapshot(namespace)
    response = SnapshotResponse(
        ok=True,
        message="Snapshot created",
        namespace=namespace,
        operation="create_snapshot"
    )
    return response

@app.get("/v1/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
def get_stats():
    response = StatsResponse(
        ok=True,
        stats=stats.get_stats(),
        operation="get_stats"
    )
    return response

@app.get("/v1/namespaces/{namespace}/keys/{key}/history", response_model=HistoryResponse, status_code=status.HTTP_200_OK)
def get_history(namespace: str, key: str):
    history = db.get_history(key, namespace)
    if history is None:
        raise MembaseException(
            status_code=404,
            code=ErrorCode.KEY_NOT_FOUND,
            message=f"No history found for key '{key}' in namespace '{namespace}'",
            recoverable=True,
            suggested_action="Ensure the key exists and that history tracking is enabled in the database configuration."
        )
    response = HistoryResponse(
        ok=True,
        history=history,
        namespace=namespace,
        operation="get_history",
        key=key
    )
    return response

@app.get("/v1/namespaces/{namespace}/size", status_code=status.HTTP_200_OK)
def get_size(namespace: str):
    size = db.get_size(namespace)
    response = SizeResponse(
        ok=True,
        size=size,
        namespace=namespace,
        operation="get_size"
    )
    return response

@app.get("/")
def root():
    return {"message": "Welcome to the Key-Value Store API. Use /docs for API documentation."}


