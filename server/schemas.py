from pydantic import BaseModel
from typing import Any, Optional

class ErrorDetail(BaseModel):
    code: str
    message: str
    recoverable: bool = True
    suggested_action: Optional[str] = None

class BaseResponse(BaseModel):
    ok: bool = True
    operation: Optional[str] = None

class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorDetail

class SetRequest(BaseModel):
    value: Any

class SetResponse(BaseResponse):
    namespace: str
    key: str
    old_value: Any
    value: Any
    transaction_depth: int

class GetResponse(BaseResponse):
    exists: bool
    namespace: str
    key: str
    value: Optional[Any] = None

class DeleteResponse(BaseResponse):
    namespace: str
    key: str
    existed: bool
    old_value: Optional[Any] = None
    value: Optional[Any] = None
    transaction_depth: int

class TransactionResponse(BaseResponse):
    namespace: str
    transaction_depth: int

class ClearResponse(BaseResponse):
    message: str

class CountRequest(BaseModel):
    value: Any

class CountResponse(BaseResponse):
    value: Any
    count: int
    namespace: str

class GetKeysResponse(BaseResponse):
    keys: list
    namespace: str

class ExistsResponse(BaseResponse):
    exists: bool
    namespace: str
    key: str

class FindRequest(BaseModel):
    value: Any

class FindResponse(BaseResponse):
    keys: list
    namespace: str

class DumpResponse(BaseResponse):
    data: dict
    namespace: str

class SnapshotResponse(BaseResponse):
    message: str
    namespace: str

class StatsResponse(BaseResponse):
    stats: dict

class HistoryResponse(BaseResponse):
    history: list
    namespace: str
    key: str

class SizeResponse(BaseResponse):
    size: int
    namespace: str