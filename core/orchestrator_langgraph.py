import os
import json
import logging
import uuid
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from dotenv import load_dotenv
from host.host_agent import HostAgent
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from functools import partial

load_dotenv()

logging.basicConfig(level=logging.INFO)

class HURequest(BaseModel):
    hu_id: str
    test_cases: Optional[List[Dict]] = None


class A2AServer:
    def __init__(self):
        self.app = FastAPI(
            title="A2A Orquestador (A2AServer)",
            description="Orquestador multiagente usando HostAgent y JSON-RPC",
            version="2.0.0"
        )
        self.AGENT_URLS = os.getenv("AGENT_URLS", "http://localhost:8001,http://localhost:8002").split(",")
        self.host_agent = HostAgent(self.AGENT_URLS)
        self.host_agent.initialize()   
        self._add_routes()

    def load_test_cases(self):
        try:
            with open("data/test_cases.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def find_hu_by_id(self, hu_id: str):
        test_cases = self.load_test_cases()
        for test_case in test_cases:
            if test_case.get("hu_id") == hu_id:
                return test_case
        return None

    def _call_agent_tool(self, input: str, client, skill_id: str):
        """
        Ejecuta la herramienta (agente remoto) con la HU como input.
        """
        hu_dict = {"hu_id": "auto", "title": input, "description": ""}
        logging.info(f"Ejecutando skill '{skill_id}' con HU: {input}")
        return client.send_task(str(uuid.uuid4()), "session-xyz", json.dumps([hu_dict], ensure_ascii=False))

    def build_tools(self):
        tools = []
        for client in self.host_agent.clients.values():
            if client.agent_card:
                for skill in client.agent_card.skills:
                    # Crear función con partial para fijar client y skill_id
                    def make_tool(client_ref, skill_ref):
                        def wrapper(input: str):
                            return self._call_agent_tool(input, client=client_ref, skill_id=skill_ref)
                        wrapper.__name__ = skill_ref
                        wrapper.__doc__ = f"Herramienta para manejar tareas relacionadas con '{skill_ref}'."
                        return wrapper
                    tools.append(make_tool(client, skill.id))
        return tools

    def _add_routes(self):
        """
        Inicializa LLM + LangGraph Agent y define endpoints.
        """
        #self.llm = ChatOllama(
        #    model="mistral",  # Ajusta si usas otro modelo
        #    temperature=0.2,
        #    base_url=os.getenv("LLM_URL", "http://localhost:11434")
        #)
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )

        self.tools = self.build_tools()

        # Prompt optimizado para forzar tool calling
        prompt = ChatPromptTemplate.from_template("""
Eres un orquestador que decide qué herramienta usar para resolver la HU.

REGLAS IMPORTANTES:
- Usa SIEMPRE una herramienta. NO respondas con texto libre.
- Elige SOLO una herramienta de la lista proporcionada.
- NO inventes herramientas, usa exactamente el nombre definido.

CRITERIOS:
- Si la HU menciona clima, temperatura o tiempo → usa herramienta `clima`.
- Si la HU menciona login, credenciales, contraseña, validación, pruebas → usa herramienta `pgp`.

FORMATO OBLIGATORIO:
No devuelvas texto libre, debes responder invocando la herramienta usando el sistema de acciones interno (Tool Call).

HU:
{messages}
""")

        self.react_agent = create_react_agent(
            tools=self.tools,
            model=self.llm,
            prompt=prompt
        )

        @self.app.post("/route-hu")
        async def route_hu(request: HURequest):
            hu_id = request.hu_id
            if not isinstance(hu_id, str) or not hu_id:
                raise HTTPException(status_code=400, detail="Falta el parámetro hu_id")

            hu_data = self.find_hu_by_id(hu_id)
            if not hu_data:
                raise HTTPException(status_code=404, detail=f"HU '{hu_id}' no encontrada en test_cases.json")

            hu_text = f"{hu_data.get('title', '')} {hu_data.get('description', '')}"
            logging.info(f"[Orquestador] Procesando HU: {hu_id} -> {hu_text}")

            # Deja que el LLM decida la herramienta
            result = self.react_agent.invoke({"messages": [{"role": "user", "content": hu_text}]})

            return result

        @self.app.get("/agents")
        async def list_agents():
            return self.host_agent.list_agents_info()

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "a2a-orquestador"}


# Instancia global para Uvicorn
server = A2AServer()
app = server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
