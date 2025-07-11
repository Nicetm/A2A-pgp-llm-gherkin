from pydantic import BaseModel, Field
from typing import Optional, Union, List, Dict


# --- Estructura del mensaje esperado dentro de params ---
class MessagePart(BaseModel):
    text: str

class Message(BaseModel):
    parts: List[MessagePart]


# --- Estructura general de una solicitud JSON-RPC ---
class A2ARequest(BaseModel):
    jsonrpc: str
    method: str
    id: Optional[str]
    params: Optional[Dict]  # usado como base flexible


# --- Solicitudes específicas con estructura interna validada ---
class SendTaskParams(BaseModel):
    message: Message

class SendTaskRequest(BaseModel):
    jsonrpc: str
    method: str = "tasks/send"
    id: Optional[str]
    params: SendTaskParams

# --- Respuesta JSON-RPC ---
class JSONRPCSuccess(BaseModel):
    state: Optional[str] = None
    message: Optional[str] = None

class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Union[str, dict]] = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[JSONRPCSuccess] = None
    error: Optional[JSONRPCError] = None


class InvalidRequestError(Exception):
    def __init__(self, message="Invalid Request", code=-32600):
        self.code = code
        self.message = message
        super().__init__(self.message)

class InternalError(Exception):
    def __init__(self, message="Internal error", code=-32603):
        self.code = code
        self.message = message
        super().__init__(self.message)


# --- Estados posibles de la tarea ---
class TaskState:
    COMPLETED = "COMPLETED"
    INPUT_REQUIRED = "INPUT_REQUIRED"
    ERROR = "ERROR"
