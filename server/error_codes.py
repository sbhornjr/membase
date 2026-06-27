from enum import Enum

class ErrorCode(str, Enum):
    # 400 Bad Request:
    INVALID_KEY = "invalid_key"
    INVALID_VALUE = "invalid_value"
    VALUE_NOT_JSON_SERIALIZABLE = "value_not_json_serializable"
    INVALID_NAMESPACE = "invalid_namespace"

    # 404 Not Found:
    KEY_NOT_FOUND = "key_not_found"
    NAMESPACE_NOT_FOUND = "namespace_not_found"

    # 409 Conflict:
    NO_ACTIVE_TRANSACTION = "no_active_transaction"
    TRANSACTION_ALREADY_ACTIVE = "transaction_already_active"
    CANNOT_UNDO = "cannot_undo"
    TRANSACTION_STATE_CONFLICT = "transaction_state_conflict"

    # 500 Internal Server Error:
    INTERNAL_ERROR = "internal_error"