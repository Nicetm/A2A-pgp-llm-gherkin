### core/task_manager.py

from abc import ABC, abstractmethod
from core.custom_types import (
    SendTaskRequest,
    JSONRPCResponse,
)

class TaskManager(ABC):
    @abstractmethod
    def on_send_task(self, request: SendTaskRequest) -> JSONRPCResponse:
        pass
