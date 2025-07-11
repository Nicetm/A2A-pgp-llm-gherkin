"""
Agente PGP independiente - Servicio para procesar HUs y generar Gherkin
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import logging
import os

# LLM via LangChain + Ollama
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Importar la lógica de generación de PGP clásica
from agents.task_manager import PGPTargetAgent
from agents.agent_card import AgentCard, AgentSkill, AgentCapabilities

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="PGP Agent Service",
    description="Servicio independiente para procesar HUs y generar Gherkin",
    version="1.0.0"
)

# Modelos Pydantic para la API
class HURequest(BaseModel):
    hu_id: str
    test_cases: Optional[List[Dict]] = None
    skill: Optional[str] = None
    hu_data: Optional[Dict] = None

class PGPResponse(BaseModel):
    status: str
    hu_id: str
    gherkin_content: str
    message: Optional[str] = None

# Instanciar el procesador PGP clásico
pgp_processor = PGPTargetAgent()

# Instanciar el modelo LLM (Ollama local)
LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")
llm = ChatOllama(
    model="llama3",
    temperature=0.2,
    base_url=LLM_URL
)

# Prompt para el LLM
PROMPT_TEMPLATE = (
    """
Eres un experto en QA. Dada la siguiente historia de usuario en formato JSON:
{test_cases}

- La respuesta debe iniciar con:  
  "Según la historia [hu_id], el formato Gherkin es:"

- Luego, presenta los pasos en formato lista, usando los conceptos en inglés (Given, When, Then), pero el texto de cada paso debe estar en español, claro y conciso, sin detalles innecesarios.

Ejemplo de respuesta esperada:

```
Según la historia XX-XXX el formato Gherkin es:

- Given: [condición inicial en español]
- When: [acción principal en español]
- Then: [resultado esperado en español]
```
    """
)

# Definir el AgentCard para este agente
# Configurar URL del agente desde variable de entorno
AGENT_URL = os.getenv("PGP_AGENT_URL", "http://localhost:5002")

AGENT_CARD = AgentCard(
    name="Agente PGP",
    description="Agente especializado en transformar HUs a Gherkin (PGP)",
    url=AGENT_URL,
    skills=[
        AgentSkill(id="pgp", name="PGP", description="Transforma HUs a Gherkin")
    ],
    capabilities=AgentCapabilities(streaming=False)
)

@app.get("/health")
async def health_check():
    """Endpoint de salud del servicio"""
    return {"status": "healthy", "service": "pgp-agent"}

@app.post("/process-hu", response_model=PGPResponse)
async def process_hu(request: HURequest):
    """
    Procesa una HU y genera el contenido Gherkin correspondiente usando LLM (Llama local)
    Si el LLM falla, usa la generación clásica como fallback.
    """
    try:
        logger.info(f"Procesando HU: {request.hu_id}")
        
        # Usar los datos de la HU enviados por el orquestador si están disponibles
        if request.hu_data:
            request.test_cases = [request.hu_data]
            logger.info(f"Usando datos de HU enviados por orquestador: {request.hu_data.get('title', '')}")
        # Si no se proporcionan test_cases, cargar desde archivo (fallback)
        elif not request.test_cases:
            from pathlib import Path
            path = Path("data/test_cases.json")
            if not path.exists():
                raise HTTPException(
                    status_code=404, 
                    detail=f"Archivo de test cases no encontrado en {path}"
                )
            with path.open("r", encoding="utf-8") as f:
                all_test_cases = json.load(f)
            request.test_cases = [c for c in all_test_cases if c.get("hu_id") == request.hu_id]
            if not request.test_cases:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No se encontraron test cases para HU: {request.hu_id}"
                )
        # --- Generación con LLM ---
        try:
            prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
            chain = prompt | llm
            # El input debe ser un string JSON legible
            input_json = json.dumps(request.test_cases, indent=2, ensure_ascii=False)
            gherkin_content = chain.invoke({"test_cases": input_json})
            # Si la respuesta es un objeto, extraer el contenido
            if hasattr(gherkin_content, 'content'):
                gherkin_content = gherkin_content.content
            if not isinstance(gherkin_content, str):
                gherkin_content = str(gherkin_content)
            return PGPResponse(
                status="success",
                hu_id=request.hu_id,
                gherkin_content=gherkin_content,
                message="PGP generado exitosamente por LLM"
            )
        except Exception as llm_exc:
            logger.error(f"Error usando LLM: {llm_exc}. Usando generación clásica.")
            # --- Fallback: generación clásica ---
            gherkin_content = pgp_processor.generate_pgp_from_test_cases(request.test_cases)
            return PGPResponse(
                status="success",
                hu_id=request.hu_id,
                gherkin_content=gherkin_content,
                message="PGP generado exitosamente por método clásico (fallback)"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando HU {request.hu_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno procesando HU: {str(e)}"
        )

@app.get("/process-hu/{hu_id}", response_model=PGPResponse)
async def process_hu_get(hu_id: str):
    """
    Procesa una HU usando GET (carga test_cases desde archivo)
    """
    request = HURequest(hu_id=hu_id)
    return await process_hu(request)

@app.get("/agent-card")
async def get_agent_card():
    """Devuelve la AgentCard de este agente (REST)"""
    return AGENT_CARD

@app.post("/jsonrpc")
async def jsonrpc(request: dict):
    """Método JSON-RPC para obtener la AgentCard"""
    if request.get("method") == "get_agent_card":
        return {"result": AGENT_CARD.dict()}
    return {"error": {"code": -32601, "message": "Method not found"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002) 