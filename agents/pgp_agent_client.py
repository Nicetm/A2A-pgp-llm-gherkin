"""
Cliente para comunicarse con el Agente PGP independiente
"""
import httpx
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

class PGPAgentClient:
    """
    Cliente para comunicarse con el servicio del Agente PGP
    """
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def process_hu(self, hu_id: str, test_cases: Optional[List[Dict]] = None) -> Dict:
        """
        Procesa una HU enviándola al agente PGP
        
        Args:
            hu_id: ID de la Historia de Usuario
            test_cases: Lista opcional de casos de prueba
            
        Returns:
            Dict: Respuesta del agente PGP
        """
        try:
            payload: Dict[str, Any] = {"hu_id": hu_id}
            if test_cases:
                payload["test_cases"] = test_cases
            
            response = await self.client.post(
                f"{self.base_url}/process-hu",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"Error HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Error comunicándose con el agente PGP: {str(e)}")
    
    async def process_hu_from_file(self, hu_id: str) -> Dict:
        """
        Procesa una HU cargando los test cases desde el archivo
        
        Args:
            hu_id: ID de la Historia de Usuario
            
        Returns:
            Dict: Respuesta del agente PGP
        """
        try:
            response = await self.client.get(f"{self.base_url}/process-hu/{hu_id}")
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"Error HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Error comunicándose con el agente PGP: {str(e)}")
    
    async def health_check(self) -> Dict:
        """
        Verifica la salud del agente PGP
        
        Returns:
            Dict: Estado del servicio
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Error en health check: {str(e)}")
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()

# Función de conveniencia para uso síncrono
def process_hu_sync(hu_id: str, base_url: str = "http://localhost:8001") -> Dict:
    """
    Versión síncrona para procesar una HU
    
    Args:
        hu_id: ID de la Historia de Usuario
        base_url: URL del agente PGP
        
    Returns:
        Dict: Respuesta del agente PGP
    """
    import asyncio
    
    async def _process():
        client = PGPAgentClient(base_url)
        try:
            return await client.process_hu_from_file(hu_id)
        finally:
            await client.close()
    
    return asyncio.run(_process()) 