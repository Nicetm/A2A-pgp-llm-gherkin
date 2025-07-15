"""
API REST Service - Punto de entrada para consumir desde Postman
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la URL del orquestador (puede venir de variable de entorno)
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8003")

# Crear la aplicación FastAPI
app = FastAPI(
    title="PGP Generator API",
    description="API REST para generar PGP desde Historias de Usuario",
    version="1.0.0"
)

# Configurar JSON con indentación para respuestas más legibles
@app.middleware("http")
async def format_json_response(request, call_next):
    response = await call_next(request)
    if hasattr(response, 'body') and response.headers.get("content-type", "").startswith("application/json"):
        # Reemplazar \n con saltos de línea reales para mejor legibilidad
        import json
        body = json.loads(response.body.decode())
        if "gherkin_content" in body and body["gherkin_content"]:
            # Mantener los \n como están, pero asegurar que el JSON esté bien formateado
            pass
        response = JSONResponse(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    return response

# Modelos para la API
class GeneratePGPRequest(BaseModel):
    hu_id: str

class GeneratePGPResponse(BaseModel):
    status: str
    hu_id: str
    gherkin_content: Optional[str] = None
    message: Optional[str] = None

@app.get("/health")
async def health_check():
    """Endpoint de salud del servicio"""
    return {"status": "healthy", "service": "pgp-api-rest"}

@app.post("/api/generate-pgp", response_model=GeneratePGPResponse)
async def generate_pgp(request: GeneratePGPRequest):
    """
    Genera PGP (Gherkin) desde una Historia de Usuario
    """
    try:
        logger.info(f"Generando PGP para HU: {request.hu_id}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/route-hu",
                json=request.model_dump()
            )
            print(f"[LangGraph] Response: {response.json()}")  
            response.raise_for_status()
            router_response = response.json()
            gherkin_content = router_response.get("gherkin_content", "")
            return GeneratePGPResponse(
                status=router_response.get("status", "error"),
                hu_id=request.hu_id,
                gherkin_content=gherkin_content,
                message=router_response.get("message")
            )
    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP del orquestador: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"No hay agente disponible para la HU '{request.hu_id}'"
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error del orquestador: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error generando PGP para HU {request.hu_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno generando PGP: {str(e)}"
        )

# Elimina los endpoints GET que requerían skill

@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "PGP Generator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/generate-pgp": "Generar PGP desde HU (JSON)",
            "GET /api/generate-pgp/{hu_id}": "Generar PGP desde HU (path parameter)",
            "GET /health": "Estado del servicio"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 