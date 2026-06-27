from fastmcp import FastMCP
import httpx
import asyncio

mcp = FastMCP("membase")

MEMBASE_API_URL = "http://localhost:8000"

@mcp.tool()
async def set_key(namespace: str, key: str, value: str) -> dict:
    """
    Creates or replaces the value for one key in a namespace.

    Use to create or update a key-value pair.
    If the task requires confirmation, call `get_key` after `set_key` to verify the value.
    If setting several keys that should be atomic, call `begin_transaction` first, then call `commit_transaction` after verification.
    If `set_key` fails inside a transaction, call `rollback_transaction` unless the user asked to keep partial changes.
    """
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}",
            json={"value": value},
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def get_key(namespace: str, key: str) -> dict:
    """
    Gets the value mapped to a key in a namespace.

    Use to get the value of a key, when you need to verify the result of a previous operation, or when you need to get a key's value for any reason.
    Check the `exists` field before using the `value`.
    If `exists` is false and the user expected the key to exist, report that the key is missing.
    If this call is part of a verification workflow and the value is not as expected, do not commit the transaction.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def delete_key(namespace: str, key: str) -> dict:
    """
    Remove a key-value pair from the namespace.

    Use this to remove a key from the namespace.
    Do not use this to remove and then add back a key with a different value. `set_key` will overwrite the value of existing keys.
    If you expected the key to be present but the `existed` field is False, a previous write + verification went wrong.
    If the `value` field is populated (i.e. not null or None) then something went wrong with the deletion.
    If the task requires confirmation, call `get_key` after `delete_key` to verify the value.
    If setting/deleting several keys that should be atomic, call `begin_transaction` first, then call `commit_transaction` after verification.
    If `delete_key` fails inside a transaction, call `rollback_transaction` unless the user asked to keep partial changes.
    """
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def begin_transaction(namespace: str) -> dict:
    """
    Starts a transaction in a namespace. Writes made after this call are staged until committed or rolled back.

    Use this before multiple writes that should succeed or fail together.
    Do not begin a transaction for a single simple write.
    Do not leave a transaction open after completing the task. Close it with `commit_transaction` or `rollback_transaction`
    After beginning a transaction, it will remain active until you call `commit_transaction` or `rollback_transaction`.
    Before committing, verify important expected values with `get_key`.
    If any step fails and the task requires atomicity, call `rollback_transaction`.
    With nested transactions, check `transaction_depth` to understand how many active transaction layers exist.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/transactions/begin",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def commit_transaction(namespace: str) -> dict:
    """
    Commits the active transaction in a namespace.

    Use this when all steps in a transaction were successfully completed to permanently apply all changes to the database.
    Do not use this if no transaction is active
    Do not call this after a failed write in the current transaction unless the user explicitly wants to keep partial changes.
    Do not call this before verifying critical values
    With nested transactions, check `transaction_depth` to understand how mant active transaction layers exist
    If more than one active transaction layers exist, the innermost transaction will be commited to the next innermost transaction
    If the response has `ok: false` and code `no_active_transaction`, do not claim that data was committed.
    If the task required a transaction but none is active, undo the relevant changes, begin a new transaction and repeat the intended writes.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/transactions/commit",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def rollback_transaction(namespace: str) -> dict:
    """
    Rolls back the active transaction in a namespace

    Use this when any steps in a transaction were NOT successfully completed to undo all changes in the current transaction.
    Do not use this if no transaction is active
    Do not use this if there were no failed writes in the current transaction or if all verifications passed
    With nested transactions, check `transaction_depth` to understand how mant active transaction layers exist
    If more than one active transaction layers exist, the innermost transaction will be rolled back and the next innermost transaction will stay intact
    If the response has `ok: false` and code `no_active_transaction`, do not claim that data was rolled back.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/transactions/rollback",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def clear_namespace(namespace: str) -> dict:
    """
    Deletes all keys in the namespace

    Use this only when the user explicitly asks to clear, reset, empty, or delete all keys in a namespace.
    Do not use this to inspect data.
    Do not use this to delete one key. Use `delete_key`.
    Do not use this as a cleanup step unless the user requested a full clear for cleanup.
    Do not call this because a query returned too many keys.
    This is a destructive operation.
    Do not call this unless specifically asked to clear the namespace. You cannot undo this.
    This does not take into account transactions. If this is called with a transaction active, the database will still be cleared and all active transactions will be abandoned. This cannot be rolled back.
    If you need to delete one key, call `delete_key` instead.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/clear",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def count_value(namespace: str, value: str) -> dict:
    """
    Gets the number of KV pairs in the namespace that have a given value

    Use this to know how many times a value appears in the namespace
    Do not use this to determine what specific keys hold the given value
    This does not give any information about which keys have the value, only how many different keys have the value
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/count",
            json={"value": value},
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def get_keys(namespace: str) -> dict:
    """
    Gets a list of all keys in the namespace

    Use this to get a list of all currently active keys in the namespace
    Do not use this to get the values of any keys
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def check_exists(namespace: str, key: str) -> dict:
    """
    Tells you whether a key currently exists in the namespace

    Use this if you need to know whether a key is currently active in the namespace but don't need to know its value
    Do not use this to get the value of the key. It will only tell you whether it exists or not
    If trying to verify `set_key` was successful, it is better to use `get_key` so you can also verify the value
    If `exists` is False but you expected True, a previous write must have gone wrong
    If `exists` is True but you expected False, a previous delete must have gone wrong
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}/exists",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def find_keys(namespace: str, value: str) -> dict:
    """
    Gets a list of all keys for a given value in a namespace

    Use this to get all keys that are mapped to a specific value in a namespace
    Do not use this for a list of all keys in the namespace - only for keys mapped to a specific value
    If trying to verify a single `set_key` was successful, it is better to use `get_key` for efficiency
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/find",
            json={"value": value},
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def dump_namespace(namespace: str) -> dict:
    """
    Gets the entire namespace as a dictionary/object

    Use this when you need to see the entire namespace
    Do not use this to check only a single KV pair
    If trying to verify a single `set_key` was successful, it is better to use `get_key` for efficiency
    If the namespace is large, it is inadvisable to use this tool
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/dump",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def create_snapshot(namespace: str) -> dict:
    """
    Saves a snapshot of the current namespace as-is for persistence

    Use this at the end of a session or whenever you need to permanently save all current changes
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/snapshot",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def get_stats() -> dict:
    """
    Gets a number of stats from the current session

    This endpoint gets the number of set operations (set_ops), get operations (get_ops), delete operations (delete_ops), 
    transaction commits (commits), transaction rollbacks (rollbacks), snapshots created (snapshots), and the current size of the write-ahead log (wal_size)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/stats",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def get_history(namespace: str, key: str) -> dict:
    """
    Get the write history of a single key

    Use this when you need to trace the history of changes to a single key
    The list returned is a list of tuples, (t, v), where t is the time that the operation was performed, and v is the value of the key after that operation
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}/history",
            timeout=5.0
        )
        return response.json()

@mcp.tool()
async def get_size(namespace: str) -> dict:
    """
    Get the size of the namespace

    Use this to determine how many total entries there are in the namespace
    Do not use this to get any keys or values, it will only give the number of entries in the namespace
    """
    async with httpx.AsyncClient() as client:
        response = httpx.get(
            f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/size",
            timeout=5.0
        )
        return response.json()

if __name__ == "__main__":
    mcp.run()

