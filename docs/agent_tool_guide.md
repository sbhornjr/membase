# membase Agent Tool Guide

membase is a key-value database with namespaces, transactions, persistence, and history.

## General rules for agents

- Always inspect the current namespace before modifying data if the task mentions a namespace.
- Use `begin_transaction` before multi-step updates that should be atomic.
- Use `rollback_transaction` if any step in a transaction fails.
- Use `commit_transaction` only after verifying all expected values are present.
- Do not call `clear` unless the user explicitly asks to remove all keys.
- If an operation returns `ok: false`, read `error.suggested_action` before retrying.

# Tools:

## Tool: set_key

Purpose:
Creates or replaces the value for one key in a namespace.

Use When:
The user asks to create or update a key.

Do Not Use:
- Do not use this to check whether a key exists. Use `get_key` or `exists_key`.
- Do not use this for multiple related writes that must succeed or fail together unless a transaction is active.
- Do not use this if the user only asks to view current data.

HTTP Endpoint: PUT "/v1/namespaces/{namespace}/keys/{key}"

MCP Tool: set_key

Path Parameters:
- namespace: The namespace/database/table-like scope to modify.
- key: The key to create or update.

Request Body:
{
  "value": "any JSON-serializable value"
}

Response Body:
{
    "ok": bool,
    "operation": "set",
    "namespace": str,
    "key": str,
    "old_value": ANY or null,
    "value": ANY,
    "transaction_depth": int
}

Agent Guidance:
- If the task requires confirmation, call `get_key` after `set_key` to verify the value.
- If setting several keys that should be atomic, call `begin_transaction` first, then call `commit_transaction` after verification.
- If `set_key` fails inside a transaction, call `rollback_transaction` unless the user asked to keep partial changes.

Common errors:
- invalid_key: The key is empty or invalid. Ask for a valid key or retry with a corrected key.
- value_not_json_serializable: The value cannot be stored as JSON. Convert it to a JSON-serializable value before retrying.

## Tool: get_key

Purpose:
Gets the value mapped to a key in a namespace.

Use When:
Use this when the user asks what value a key has, when you need to verify the result of a previous operation, or when you need to get a key's value for any reason.

Do Not Use:
- Do not use this to list all keys. Use `list_keys`.
- Do not treat a missing key as an internal failure. Missing keys are normal database state.

HTTP Endpoint: GET "/v1/namespaces/{namespace}/keys/{key}"

MCP Tool: get_key

Path Parameters:
- namespace: The namespace/database/table-like scope to search in.
- key: The key whose value you want to retrieve.

Response Body:
{
    "ok": bool,
    "operation": "get",
    "namespace": str,
    "key": str,
    "exists": bool,
    "value": ANY or null
}

Agent guidance:
- Check the `exists` field before using the `value`.
- If `exists` is false and the user expected the key to exist, report that the key is missing.
- If this call is part of a verification workflow and the value is not as expected, do not commit the transaction.

## Tool: delete_key

Purpose:
Remove a key-value pair from the namespace.

Use When:
Use this when the user asks to remove a key from the namespace.

Do Not Use:
- Do not use this to remove and then add back a key with a different value. `set_key` will overwrite the value of existing keys.

HTTP Endpoint: DELETE "/v1/namespaces/{namespace}/keys/{key}"

MCP Tool: delete_key

Path Parameters:
- namespace: The namespace/database/table-like scope to delete in.
- key: The key you want to delete.

Response Body:
{
    "ok": bool,
    "operation": "delete",
    "namespace": str,
    "key": str,
    "existed": bool,
    "old_value": ANY or null,
    "value": ANY or null,
    "transaction_depth": int
}

Agent Guidance:
- If you expected the key to be present but the `existed` field is False, a previous write + verification went wrong.
- If the `value` field is populated (i.e. not null or None) then something went wrong with the deletion.
- If the task requires confirmation, call `get_key` after `delete_key` to verify the value.
- If setting/deleting several keys that should be atomic, call `begin_transaction` first, then call `commit_transaction` after verification.
- If `delete_key` fails inside a transaction, call `rollback_transaction` unless the user asked to keep partial changes.

## Tool: begin_transaction

Purpose:
Starts a transaction in a namespace. Writes made after this call are staged until committed or rolled back.

Use When:
Use this before multiple writes that should succeed or fail together.

Do Not Use:
- Do not begin a transaction for a single simple write.
- Do not begin a transaction if the user only asked to inspect data.
- Do not leave a transaction open after completing the task.

HTTP Endpoint: GET "/v1/namespaces/{namespace}/transactions/begin"

MCP Tool: begin_transaction

Path Parameters:
- namespace: The namespace scope to begin the transaction in.

Response Body:
{
    "ok": bool,
    "operation": "begin_transaction",
    "transaction_depth": int,
    "namespace": str
}

Agent Guidance:
- After beginning a transaction, it will remain active until you call `commit_transaction` or `rollback_transaction`.
- Before committing, verify important expected values with `get_key`.
- If any step fails and the task requires atomicity, call `rollback_transaction`.
- With nested transactions, check `transaction_depth` to understand how many active transaction layers exist.

## Tool: commit_transaction

Purpose:
Commits the active transaction in a namespace.

Use When:
Use this when all steps in a transaction were successfully completed to permanently apply all changes to the database.

Do Not Use:
- Do not use this if no transaction is active
- Do not call this after a failed write in the current transaction unless the user explicitly wants to keep partial changes.
- Do not call this before verifying critical values

HTTP Endpoint: GET "/v1/namespaces/{namespace}/transactions/commit"

MCP Tool: commit_transaction

Path Parameters:
- namespace: The namespace scope to commit the transaction in.

Response Body:
{
    "ok": bool,
    "operation": "commit_transaction",
    "transaction_depth": int,
    "namespace": str
}

Agent Guidance:
- With nested transactions, check `transaction_depth` to understand how mant active transaction layers exist
- If more than one active transaction layers exist, the innermost transaction will be commited to the next innermost transaction
- If the response has `ok: false` and code `no_active_transaction`, do not claim that data was committed.
- If the task required a transaction but none is active, undo the relevant changes, begin a new transaction and repeat the intended writes.

## Tool: rollback_transaction

Purpose:
Rolls back the active transaction in a namespace

Use When:
Use this when any steps in a transaction were NOT successfully completed to undo all changes in the current transaction.

Do Not Use:
- Do not use this if no transaction is active
- Do not use this if there were no failed writes in the current transaction or if all verifications passed

HTTP Endpoint: GET "/v1/namespaces/{namespace}/transactions/rollback"

MCP Tool: rollback_transaction

Path Parameters:
- namespace: The namespace scope to rollback the transaction in.

Response Body:
{
    "ok": bool,
    "operation": "rollback_transaction",
    "transaction_depth": int,
    "namespace": str
}

Agent Guidance:
- With nested transactions, check `transaction_depth` to understand how mant active transaction layers exist
- If more than one active transaction layers exist, the innermost transaction will be rolled back and the next innermost transaction will stay intact
- If the response has `ok: false` and code `no_active_transaction`, do not claim that data was rolled back.

## Tool: clear_namespace

Purpose:
Deletes all keys in the namespace

Use When:
Use this only when the user explicitly asks to clear, reset, empty, or delete all keys in a namespace.

Do Not Use:
- Do not use this to inspect data.
- Do not use this to delete one key. Use `delete_key`.
- Do not use this as a cleanup step unless the user requested a full clear for cleanup.
- Do not call this because a query returned too many keys.

HTTP Endpoint: GET "/v1/namespaces/{namespace}/clear"

MCP Tool: clear_database

Path Parameters:
- namespace: The namespace scope to clear

Response Body:
{
    "ok": bool,
    "operation": "clear_namespace",
    "message": "Namespace cleared"
}

Agent Guidance:
- This is a destructive operation.
- Do not call this unless specifically asked to clear the namespace. You cannot undo this.
- This does not take into account transactions. If this is called with a transaction active, the namespace will still be cleared and all active transactions will be abandoned. This cannot be rolled back.
- If the user asks to remove one key, call `delete_key` instead.

## Tool: count_value

Purpose: 
Gets the number of KV pairs in the namespace that have a given value

Use When:
Use this to know how many times a value appears in the namespace

Do Not Use:
- Do not use this to determine what specific keys hold the given value
- Do not use this for any writes - this is only a read operation

HTTP Endpoint: POST "/v1/namespaces/{namespace}/count"

Path Parameters:
- namespace: The namespace scope to count values in.

Request Body:
{
  "value": "any JSON-serializable value"
}

Response Body:
{
    "ok": bool,
    "operation": "count_value",
    "namespace": str,
    "value": ANY,
    "count": int
}

Agent Guidance:
- This does not give any information about which keys have the value, only how many different keys have the value

## Tool: get_keys

Purpose:
Gets a list of all keys in the namespace

Use When:
Use this to get a list of all currently active keys in the namespace

Do Not Use:
- Do not use this to get the values of any keys
- Do not use this for any writes - this is only a read operation

HTTP Endpoint: GET "/v1/namespaces/{namespace}/keys"

MCP Tool: get_keys

Path Parameters:
- namespace: The namespace scope to get the keys of

Response Body:
{
    "ok": bool,
    "operation": "get_keys",
    "namespace": str,
    "keys" str[]
}

Agent Guidance:
- This does not give any information about the values of the keys

## Tool: check_exists

Purpose:
Tells you whether a key currently exists in the namespace

Use When:
Use this if you need to know whether a key is currently active in the namespace but don't need to know its value

Do Not Use:
- Do not use this to get the value of the key. It will only tell you whether it exists or not
- Do not use this for any writes - this is only a read operation

HTTP Endpoint: GET "/v1/namespaces/{namespace}/keys/{key}/exists"

MCP Tool: check_exists

Path Parameters:
- namespace: The namespace scope to check the existence of a key in
- key: The key to check the existence of

Response Body:
{
    "ok": bool,
    "operation": "check_exists",
    "namespace": str,
    "key": str,
    "exists": bool
}

Agent Guidance:
- This does not give any information about the values of the key
- If trying to verify `set_key` was successful, it is better to use `get_key` so you can also verify the value
- If `exists` is False but you expected True, a previous write must have gone wrong
- If `exists` is True but you expected False, a previous delete must have gone wrong

## Tool: find_keys

Purpose:
Gets a list of all keys for a given value in a namespace

Use When:
Use this to get all keys that are mapped to a specific value in a namespace

Do Not Use:
- Do not use this for a list of all keys in the namespace - only for keys mapped to a specific value
- Do not use this for any writes - this is only a read operation

HTTP Endpoint: POST "/v1/namespaces/{namespace}/find"

MCP Tool: find_keys

Path Parameters:
- namespace: The namespace scope to get keys in

Request Body:
{
  "value": "any JSON-serializable value"
}

Response Body:
{
    "ok": bool,
    "operation": "find_keys",
    "namespace": str,
    "keys": str[]
}

Agent Guidance:
- If trying to verify a single `set_key` was successful, it is better to use `get_key` for efficiency

## Tool: dump_namespace

Purpose:
Gets the entire namespace as a dictionary/object

Use When:
Use this when you need to see the entire namespace

Do Not Use:
- Do not use this to check only a single KV pair
- Do not use this for any writes - this is only a read operation

HTTP Endpoint: GET "/v1/namespaces/{namespace}/dump"

MCP Tool: dump_namespace

Path Parameters:
- namespace: The namespace to get the dict of

Response Body:
{
    "ok": bool,
    "operation": "dump_namespace",
    "namespace": str,
    "data": dictionary
}

Agent Guidance:
- If trying to verify a single `set_key` was successful, it is better to use `get_key` for efficiency
- If the namespace is large, it is inadvisable to use this endpoint

## Tool: create_snapshot

Purpose:
Saves a snapshot of the current namespace as-is for persistence

Use When:
Use this at the end of a session or whenever you need to permanently save all current changes

HTTP Endpoint: GET "/v1/namespaces/{namespace}/snapshot"

MCP Tool: create_snapshot

Path Parameters:
- namespace: The namespace to save a snapshot of

Response Body:
{
    "ok": bool,
    "operation": "create_snapshot",
    "namespace": str,
    "message": "Snapshot created"
}

## Tool: get_stats

Purpose:
Gets a number of stats from the current session

Use When:
Use this to get a number of interesting stats for the session

HTTP Endpoint: GET "/v1/stats"

MCP Tool: get_stats

Response Body:
{
    "ok": bool,
    "operation": "get_stats"
    "stats": {
        "set_ops": int,
        "get_ops": int,
        "delete_ops": int,
        "commits": int,
        "rollbacks": int,
        "snapshots": int,
        "wal_size": int
    }
}

Agent Guidance:
- This endpoint gets the number of set operations, get operations, delete operations, transaction commits, transaction rollbacks, snapshots created, and the current size of the write-ahead log

## Tool: get_history

Purpose:
Get the write history of a single key in a namespace

Use When:
Use this when you need to trace the history of changes to a single key

HTTP Endpoint: GET "/v1/namespaces/{namespace}/keys/{key}/history"

MCP Tool: get_history

Path Parameters:
- namespace: The namespace to look in
- key: The key to get the history of

Response Body:
{
    "ok": bool,
    "operation": "get_history"
    "namespace": str,
    "key": str,
    "history": List
}

Agent Guidance:
- The list returned is a list of tuples, (t, v), where t is the time that the operation was performed, and v is the value of the key after that operation

## Tool: get_size

Purpose:
Get the size of the namespace

Use When:
Use this to determine how many total entries there are in the namespace

Do Not Use:
- Do not use this to get any keys or values, it will only give the number of entries in the namespace

HTTP Endpoint: GET "/v1/namespaces/{namespace}/size"

MCP Tool: get_size

Path Parameters:
- namespace: The namespace to look in

Response Body:
{
    "ok": bool,
    "operation": "get_size",
    "namespace": str,
    "size": int
}

# Common Workflows:

### Set and verify a key

1. Call `set_key`.
2. Call `get_key` for the same namespace and key.
3. Check that the `exists` value is true and the `value` field matches the requested value.
4. Success only after the verification passes.

### Atomic update

1. Call `begin_transaction`.
2. Perform writes.
3. Verify values.
4. If all verification passes, call `commit_transaction`.
5. If any verification fails, call `rollback_transaction`.

### Delete a key

1. Call `delete_key`.
2. Call `get_key` for the same namespace and key.
3. You should get an error with http code 404 and code 'key_not_found'.
