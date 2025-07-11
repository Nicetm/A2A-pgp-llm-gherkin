"""
Orquestador multiagente para Agentic RAG
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import os
import logging
import json
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs de los agentes registrados (pueden venir de env o docker-compose)
AGENT_URLS = os.getenv("AGENT_URLS", "http://localhost:8001,http://localhost:8002").split(",")

app = FastAPI(
    title="Orquestador Agentic RAG",
    description="Orquestador multiagente para Agentic RAG",
    version="1.0.0"
)

class HURequest(BaseModel):
    hu_id: str
    test_cases: Optional[List[Dict]] = None

def load_test_cases():
    """Carga los casos de prueba desde el archivo JSON"""
    try:
        with open("data/test_cases.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando test_cases.json: {e}")
        return []

def find_hu_by_id(hu_id: str) -> Optional[Dict]:
    """Busca una HU por su ID en test_cases.json"""
    test_cases = load_test_cases()
    for test_case in test_cases:
        if test_case.get("hu_id") == hu_id:
            return test_case
    return None

def determine_skill_from_hu_text(hu_text: str) -> Optional[str]:
    """Determina la skill basándose en el texto de la HU"""
    hu_text_lower = hu_text.lower()
    
    # Buscar palabras clave para determinar la skill
    if "clima" in hu_text_lower or "temperatura" in hu_text_lower or "tiempo" in hu_text_lower:
        return "clima"
    elif any(keyword in hu_text_lower for keyword in ["pgp", "login", "ingresar", "acceder", "contraseña", "usuario"]):
        return "pgp"
    else:
        return None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orquestador"}

@app.get("/agents")
async def list_agents():
    """Devuelve los AgentCard de todos los agentes registrados"""
    agent_cards = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in AGENT_URLS:
            try:
                resp = await client.get(f"{url}/agent-card")
                resp.raise_for_status()
                agent_cards.append(resp.json())
            except Exception as e:
                logger.error(f"No se pudo consultar {url}: {e}")
    return agent_cards

@app.post("/route-hu")
async def route_hu(request: HURequest):
    """
    Recibe una HU, decide la skill y la reenvía al agente con la skill adecuada.
    """
    # 1. Buscar la HU en test_cases.json usando el hu_id
    hu_data = find_hu_by_id(request.hu_id)
    if not hu_data:
        raise HTTPException(status_code=404, detail=f"HU '{request.hu_id}' no encontrada en test_cases.json")
    
    # 2. Obtener el texto de la HU para determinar la skill
    hu_text = f"{hu_data.get('title', '')} {hu_data.get('description', '')}"
    
    # 3. Determinar la skill basándose en el texto de la HU
    skill = determine_skill_from_hu_text(hu_text)
    if not skill:
        raise HTTPException(status_code=404, detail=f"No hay agente disponible para la HU '{request.hu_id}' con texto: '{hu_text}'")
    
    logger.info(f"HU '{request.hu_id}' asignada a skill '{skill}' basándose en texto: '{hu_text}'")
    
    # 4. Consultar los AgentCard
    agent_cards = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in AGENT_URLS:
            try:
                resp = await client.get(f"{url}/agent-card")
                resp.raise_for_status()
                card = resp.json()
                card["url"] = url  # Asegura que la URL sea la correcta
                agent_cards.append(card)
            except Exception as e:
                logger.error(f"No se pudo consultar {url}: {e}")
    
    # 5. Buscar agente con la skill adecuada
    for card in agent_cards:
        for s in card.get("skills", []):
            if s["id"] == skill:
                # 6. Reenviar la HU al agente correcto
                try:
                    logger.info(f"Enviando HU {request.hu_id} a {card['name']} ({card['url']})")
                    # Añadir skill y datos de la HU al request para el agente
                    req = request.model_dump()
                    req["skill"] = skill
                    req["hu_data"] = hu_data  # Incluir los datos completos de la HU
                    
                    # Crear un nuevo cliente para enviar la petición
                    async with httpx.AsyncClient(timeout=30.0) as send_client:
                        resp = await send_client.post(f"{card['url']}/process-hu", json=req)
                        resp.raise_for_status()
                        return resp.json()
                except Exception as e:
                    logger.error(f"Error enviando HU al agente {card['name']}: {e}")
                    raise HTTPException(status_code=500, detail=f"Error enviando HU al agente {card['name']}: {e}")
    
    # 7. Si no hay agente con la skill
    raise HTTPException(status_code=404, detail=f"No hay agente disponible para la HU '{request.hu_id}'")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 