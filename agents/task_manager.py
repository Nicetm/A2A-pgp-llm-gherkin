### agents/task_manager.py
import json
import traceback

from core.task_base import TaskManager
from core.custom_types import (
    JSONRPCResponse,
    JSONRPCSuccess,
    JSONRPCError,
    TaskState,
)

# Esta clase manejará la lógica para transformar casos de prueba en PGPs en lenguaje Gherkin
class PGPTargetAgent(TaskManager):
    def __init__(self):
        super().__init__()

    def on_send_task(self, request) -> JSONRPCResponse:
        try:
            # Extrae el contenido del mensaje desde la estructura esperada
            message = request.params.message.parts[0].text
            test_cases = json.loads(message)
            pgp_output = self.generate_pgp_from_test_cases(test_cases)

            return JSONRPCResponse(
                id=request.id,
                result=JSONRPCSuccess(
                    state=TaskState.COMPLETED,
                    message=pgp_output,
                )
            )
        except Exception as e:
            import traceback
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(
                    code=-32000,
                    message="Error al procesar on_send_task",
                    data=traceback.format_exc(),
                )
            )
    
    def generate_pgp_from_test_cases(self, test_cases: list[dict]) -> str:
        scenarios = []

        for case in test_cases:
            hu_id = case.get("hu_id", "")
            title = case.get("title", "")
            description = case.get("description", "")
            preconditions = case.get("preconditions", [])
            steps = case.get("steps", [])
            expected_result = case.get("expected_result", "")

            lines = []

            # Comentarios con metadata
            if hu_id or title:
                lines.append(f"# {hu_id} - {title}")
            if description:
                lines.append(f"# {description}")
            lines.append("")  # línea vacía

            lines.append(f"Scenario: {title}")

            # GIVEN: precondiciones
            if preconditions:
                lines.append(f"  Given {preconditions[0]}")
                for pre in preconditions[1:]:
                    lines.append(f"  And {pre}")

            # WHEN: pasos
            if steps:
                lines.append(f"  When {steps[0]}")
                for step in steps[1:]:
                    lines.append(f"  And {step}")

            # THEN: resultado esperado
            if expected_result:
                lines.append(f"  Then {expected_result}")

            scenarios.append("\n".join(lines))

        return "\n\n".join(scenarios)




