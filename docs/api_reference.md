## AVAILABLE APIs:

All API documentation is available via OpenAPI at `/openapi.json` or through Swagger UI at `/docs`.

- PUT "/v1/namespaces/{namespace}/keys/{key}"
    - Request: {"value": ANY}
    - Response: {"ok": bool, "operation": "set", "namespace": str, "key": str, "value": ANY, "transaction_depth": int}
    - Creates an entry in the KV store of "key": value in namespace "namespace"
- GET "/v1/namespaces/{namespace}/keys/{key}"
    - Response: {"ok": bool, "operation": "get", "namespace": str, "key": str, "exists": bool, "value": ANY}
    - Retrieves the value associated with the key "key" in namespace "namespace"
- DELETE "/v1/namespaces/{namespace}/keys/{key}"
    - Response: {"ok": bool, "operation": "delete", "namespace": str, "key": str, "existed": bool, "old_value": ANY, "new_value": None, "transaction_depth": int}
    - Deletes entry associated with the key "key" in namespace "namespace"
- GET "/v1/namespaces/{namespace}/transactions/begin"
    - Response: {"ok": bool, "operation": "begin_transaction", "namespace": str, "transaction_depth": int}
    - Begins a transaction in namespace "namespace"
- GET "/v1/namespaces/{namespace}/transactions/commit"
    - Response: {"ok": bool, "operation": "commit_transaction", "namespace": str, "transaction_depth": int}
    - Commits the innermost transaction in namespace "namespace"
- GET "/v1/namespaces/{namespace}/transactions/rollback"
    - Response: {"ok": bool, "operation": "rollback_transaction", "namespace": str, "transaction_depth": int}
    - Rolls back the innermost transaction in namespace "namespace"
- GET "/v1/namespaces/{namespace}/clear"
    - Response: {"ok": bool, "operation": "clear_namespace", "message": "Namespace cleared."}
    - Clears the entire namespace of all keys and values
    - NOTE: This also clears all active transactions, meaning a clear is not considered part of a transaction. This cannot be rolled back.
- POST "/v1/namespaces/{namespace}/count"
    - Request: {"value": ANY}
    - Response: {"ok": bool, "operation": "count_value", "namespace": str, "value": ANY, "count": int}
    - Finds the number of keys in namespace "namespace" that are associated with value "value"
- GET "/v1/namespaces/{namespace}/keys"
    - Response: {"ok": bool, "operation": "get_keys", "namespace": str, "keys": str[]}
    - Retrieves a list of keys from the database in the given namespace
- GET "/v1/namespaces/{namespace}/keys/{key}/exists"
    - Response: {"ok": bool, "operation": "check_exists", "namespace": str, "key": str, "exists": bool}
    - Determines whether key "key" currently exists in namespace "namespace"
- POST "/v1/namespaces/{namespace}/find"
    - Request: {"value": ANY}
    - Response: {"ok": bool, "operation": "find_keys", "namespace": str, "keys": str[]}
    - Retrieves a list of keys from the database in the given namespace associated with the given value
- GET "/v1/namespaces/{namespace}/dump"
    - Response: {"ok": bool, "operation": "dump_namespace", "namespace": str, "data": {}}
    - Retrieves the entire KV store in namespace "namespace" as a dict
- GET "/v1/namespaces/{namespace}/snapshot"
    - Response: {"ok": bool, "operation": "create_snapshot", "namespace": str, "message": "Snapshot created"}
    - Forces a snapshot creation for the namespace for persistence. A snapshot will automatically be created after a number of operations anyway, but it is recommended to use this at the end of a session anyway.
- GET "/v1/namespaces/{namespace}/stats"
    - Response: {"ok": bool, "operation": "get_stats", "namespace": str, "stats": {}}
    - Retrieves stats of the current session including "set_ops", "get_ops", "delete_ops", "commits", "rollbacks", "snapshots" and "wal_size"
- GET "/v1/namespaces/{namespace}/keys/{key}/history"
    - Response: {"ok": bool, "operation": "get_history", "namespace": str, "key": str, "history": []}
    - Retrieves the history of the given key in namespace "namespace" as a list of tuples, where the first item is the time it was changed and the second item is the value at that time
- GET "/v1/namespaces/{namespace}/size"
    - Response: {"ok": bool, "operation": "get_size", "namespace": str, "size": int}
    - Retrieves the number of keys in namespace "namespace"

Finally, if an error is caught and returned, it will be in this format:
{"ok": False, "error": {"code": str, "message": str, "recoverable": bool, "suggested_action": str}}