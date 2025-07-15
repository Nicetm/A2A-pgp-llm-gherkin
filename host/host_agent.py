# host/host_agent.py
import uuid
import json
from typing import List, Optional, Dict
from pathlib import Path
from core.custom_types import TaskState
from host.remote_agent_client import RemoteAgentClient

class HostAgent:
    """
    Clase responsable de gestionar múltiples agentes remotos y coordinar el envío de tareas,
    así como la consulta de información sobre los agentes disponibles.
    """
    def __init__(self, remote_addresses: List[str]):
        """
        Inicializa el HostAgent creando clientes remotos para cada dirección proporcionada.
        Args:
            remote_addresses (List[str]): Lista de direcciones de los agentes remotos.
        """
        self.clients: Dict[str, RemoteAgentClient] = {}
        for addr in remote_addresses:
            self.clients[addr] = RemoteAgentClient(addr)

    def initialize(self):
        """
        Inicializa todos los clientes remotos obteniendo la tarjeta de agente de cada uno.
        """
        for addr, client in self.clients.items():
            client.fetch_agent_card()

    def list_agents_info(self) -> list:
        """
        Devuelve una lista con la información de todos los agentes registrados.
        Returns:
            list: Información relevante de cada agente (nombre, descripción, url, etc).
        """
        infos = []
        for addr, c in self.clients.items():
            card = c.agent_card
            if card:
                infos.append({
                    "name": card.name,
                    "description": card.description,
                    "url": card.url,
                    "streaming": card.capabilities.streaming,
                    "skills": [s.id for s in card.skills]
                })
            else:
                infos.append({
                    "name": "Unknown",
                    "description": "Not loaded",
                    "url": addr,
                    "streaming": False,
                    "skills": []
                })
        return infos

    def get_client_by_skill(self, skill_id: str) -> Optional[RemoteAgentClient]:
        """
        Busca y retorna el cliente remoto que soporte una habilidad específica.
        Args:
            skill_id (str): ID de la habilidad buscada.
        Returns:
            Optional[RemoteAgentClient]: Cliente que soporta la habilidad, o None si no existe.
        """
        for client in self.clients.values():
            if client.agent_card:
                for skill in client.agent_card.skills:
                    if skill.id == skill_id:
                        return client
        return None

    def send_task_by_skill(self, skill_id: str, message: str) -> dict:
        """
        Envía una tarea a un agente que soporte la habilidad indicada.
        Args:
            skill_id (str): ID de la habilidad requerida.
            message (str): Mensaje o payload de la tarea.
        Returns:
            dict: Resultado de la operación o mensaje de error.
        """
        client = self.get_client_by_skill(skill_id)
        if not client:
            return {
                "status": "error",
                "gherkin_content": f"No agent supports skill '{skill_id}'.",
                "message": "No se encontró agente para la skill solicitada"
            }

        task_id = str(uuid.uuid4())
        session_id = "session-xyz"

        try:
            result = client.send_task(task_id, session_id, message)
            if isinstance(result, dict):
                return result
            else:
                return {
                    "status": "success",
                    "gherkin_content": result,
                    "message": "PGP generado exitosamente"
                }
        except Exception as exc:
            return {
                "status": "error",
                "gherkin_content": f"Remote agent call failed: {exc}",
                "message": "Error llamando al agente remoto"
            }

    def send_task_by_hu(self, hu_id: str) -> str:
        """
        Envía una tarea a un agente usando los casos de prueba filtrados por HU (Historia de Usuario).
        Args:
            hu_id (str): ID de la Historia de Usuario.
        Returns:
            str: Resultado de la operación o mensaje de error.
        """
        try:
            # Carga los test cases
            path = Path("data/test_cases.json")
            if not path.exists():
                return f"Archivo {path} no encontrado."

            with path.open("r", encoding="utf-8") as f:
                test_cases = json.load(f)

            # Filtra los casos por hu_id
            filtered = [c for c in test_cases if c["hu_id"] == hu_id]
            if not filtered:
                return f"No se encontraron casos para HU = {hu_id}"

            # Toma el primer agente disponible
            client = None
            for c in self.clients.values():
                if c.agent_card:
                    client = c
                    break

            if not client:
                return "No se encontró ningún agente con AgentCard cargado."

            task_id = str(uuid.uuid4())
            session_id = "session-pgp"

            message = json.dumps(filtered, indent=2)
            # Envia el mensaje al agente remoto con el payload de los test cases filtrados por HU
            result = client.send_task(task_id, session_id, message)
            return f"Tarea enviada: {result}"

        except Exception as e:
            return f"Error al enviar tarea: {e}"
        
    def get_default_agent(self) -> Optional[RemoteAgentClient]:
        """
        Retorna el primer agente disponible que tenga AgentCard cargado.
        Returns:
            Optional[RemoteAgentClient]: El primer agente válido o None si no hay ninguno.
        """
        for client in self.clients.values():
            if client.agent_card:
                return client
        return None