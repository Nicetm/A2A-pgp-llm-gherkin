"""
Agente Clima - Servicio de ejemplo para responder sobre clima
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import os
from agents.agent_card import AgentCard, AgentSkill, AgentCapabilities

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agente Clima",
    description="Agente de ejemplo para responder sobre clima",
    version="1.0.0"
)

class HURequest(BaseModel):
    hu_id: str
    skill: Optional[str] = None
    test_cases: Optional[List[Dict]] = None
    hu_data: Optional[Dict] = None

class ClimaResponse(BaseModel):
    status: str
    hu_id: str
    clima: Optional[str] = None
    message: Optional[str] = None

# Configurar URL del agente desde variable de entorno
AGENT_URL = os.getenv("CLIMA_AGENT_URL", "http://localhost:5003")

AGENT_CARD = AgentCard(
    name="Agente Clima",
    description="Agente especializado en responder sobre clima",
    url=AGENT_URL,
    skills=[
        AgentSkill(id="clima", name="Clima", description="Responde preguntas sobre el clima")
    ],
    capabilities=AgentCapabilities(streaming=False)
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agente-clima"}

@app.get("/agent-card")
async def get_agent_card():
    return AGENT_CARD

@app.post("/jsonrpc")
async def jsonrpc(request: dict):
    if request.get("method") == "get_agent_card":
        return {"result": AGENT_CARD.dict()}
    return {"error": {"code": -32601, "message": "Method not found"}}

@app.post("/process-hu", response_model=ClimaResponse)
async def process_hu(request: HURequest):
    if request.skill != "clima":
        return ClimaResponse(
            status="error",
            hu_id=request.hu_id,
            clima=None,
            message="Este agente solo responde a skills de clima."
        )
    
    # Usar los datos de la HU si están disponibles para personalizar la respuesta
    hu_title = request.hu_data.get('title', '') if request.hu_data else ''
    hu_description = request.hu_data.get('description', '') if request.hu_data else ''
    
    logger.info(f"Procesando consulta de clima para HU: {request.hu_id} - {hu_title}")
    
    # Respuesta simulada
    return ClimaResponse(
        status="success",
        hu_id=request.hu_id,
        clima="Soleado y 25°C",
        message=f"Respuesta generada por Agente Clima para: {hu_title}"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003) 