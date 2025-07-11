import requests
from agents.agent_card import AgentCard

class RemoteAgentClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.agent_card: AgentCard | None = None

    def fetch_agent_card(self):
        try:
            url = f"{self.base_url}/.well-known/agent.json"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            self.agent_card = AgentCard(**data)
        except Exception as e:
            print(f"No se pudo obtener agent.json desde {self.base_url}: {e}")
            self.agent_card = None

    def send_task(self, task_id: str, session_id: str, message: str):
        if not self.agent_card:
            raise RuntimeError("Agente remoto no inicializado")

        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "id": task_id,
            "params": {
                "session_id": session_id,
                "message": {
                    "parts": [{"text": message}]
                }
            }
        }

        url = f"{self.base_url}/jsonrpc"
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("result") or response.json().get("error")
