import httpx
from json.decoder import JSONDecodeError

MEMBASE_API_URL = "http://localhost:8000"

TOOLS = [
    {
        "name": "set_key",
        "description": "Creates or replaces the value for one key in a namespace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "key": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["namespace", "key", "value"]
        }
    },
    {
        "name": "get_key",
        "description": "Gets the value mapped to a key in a namespace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "key": {"type": "string"}
            },
            "required": ["namespace", "key"]
        }
    },
    {
        "name": "delete_key",
        "description": "Remove a key-value pair from the namespace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "key": {"type": "string"}
            },
            "required": ["namespace", "key"]
        }
    },
    {
        "name": "begin_transaction",
        "description": "Starts a transaction in a namespace. Writes made after this call are staged until committed or rolled back.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"]
        }
    },
    {
        "name": "commit_transaction",
        "description": "Commits the active transaction in a namespace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"]
        }
    },
    {
        "name": "rollback_transaction",
        "description": "Rolls back the active transaction in a namespace",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"]
        }
    },
    {
        "name": "clear_database",
        "description": "Deletes all keys in the database",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "count_value",
        "description": "Gets the number of KV pairs in the namespace that have a given value",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["namespace", "value"]
        }
    },
    {
        "name": "get_keys",
        "description": "Gets a list of all keys in the namespace",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"]
        }
    },
    {
        "name": "check_exists",
        "description": "Tells you whether a key currently exists in the namespace",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "key": {"type": "string"}
            },
            "required": ["namespace", "key"]
        }
    },
    {
        "name": "find_keys",
        "description": "Gets a list of all keys for a given value in a namespace",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["namespace", "value"]
        }
    },
    {
        "name": "dump_database",
        "description": "Gets the entire namespace as a dictionary/object",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"]
        }
    },
    {
        "name": "create_snapshot",
        "description": "Saves a snapshot of the current namespace as-is for persistence",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"]
        }
    },
    {
        "name": "get_stats",
        "description": "Gets a number of stats from the current session",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_history",
        "description": "Get the write history of a single key",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "key": {"type": "string"}
            },
            "required": ["namespace", "key"]
        }
    },
    {
        "name": "get_size",
        "description": "Get the size of the namespace",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"]
        }
    }
]

async def execute_tool(tool_name: str, tool_input: dict) -> dict:
    namespace = tool_input.get("namespace")
    key = tool_input.get("key")
    value = tool_input.get("value")
    try:
        async with httpx.AsyncClient() as client:
            match tool_name:
                case "set_key":
                    response = await client.put(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}",
                        json={"value": value},
                        timeout=5.0
                    )
                    return response.json()
                case "get_key":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}",
                        timeout=5.0
                    )
                    return response.json()
                case "delete_key":
                    response = await client.delete(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}",
                        timeout=5.0
                    )
                    return response.json()
                case "begin_transaction":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/transactions/begin",
                        timeout=5.0
                    )
                    return response.json()
                case "commit_transaction":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/transactions/commit",
                        timeout=5.0
                    )
                    return response.json()
                case "rollback_transaction":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/transactions/rollback",
                        timeout=5.0
                    )
                    return response.json()
                case "clear_namespace":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/clear",
                        timeout=5.0
                    )
                    return response.json()
                case "count_value":
                    response = await client.post(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/count",
                        json={"value": value},
                        timeout=5.0
                    )
                    return response.json()
                case "get_keys":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys",
                        timeout=5.0
                    )
                    return response.json()
                case "check_exists":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}/exists",
                        timeout=5.0
                    )
                    return response.json()
                case "find_keys":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}/exists",
                        timeout=5.0
                    )
                    return response.json()
                case "dump_database":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/dump",
                        timeout=5.0
                    )
                    return response.json()
                case "create_snapshot":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/snapshot",
                        timeout=5.0
                    )
                    return response.json()
                case "get_stats":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/stats",
                        timeout=5.0
                    )
                    return response.json()
                case "get_history":
                    response = await client.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}/history",
                        timeout=5.0
                    )
                    return response.json()
                case "get_size":
                    response = httpx.get(
                        f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/size",
                        timeout=5.0
                    )
                    return response.json()
                case _:
                    return {"error": f"Unknown tool: {tool_name}"} 
    except JSONDecodeError as e:
        print("RESPONSE: " + response)
        raise e

async def grade(expected_state: dict) -> dict:
    results = {}
    async with httpx.AsyncClient() as http_client:
        for check in expected_state:
            namespace = check["namespace"]
            key = check["key"]
            expected_value = check.get("expected_value", None)
            expected_exists = check.get("expected_exists", True)

            response = await http_client.get(
                f"{MEMBASE_API_URL}/v1/namespaces/{namespace}/keys/{key}",
                timeout=5.0
            )
            actual = response.json()

            if not expected_exists and not actual.get("exists"):
                passed = True
            else:
                passed = actual.get("value") == expected_value
            results[f"{namespace}/{key}"] = {
                "passed": passed,
                "expected": expected_value,
                "actual": actual.get("value")
            }
    return results