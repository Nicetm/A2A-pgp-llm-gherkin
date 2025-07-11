# A2A PGP Gherkin

Este proyecto implementa una arquitectura de microservicios multi-agente para transformar Historias de Usuario (HU) en formato Jira a Gherkin, usando FastAPI y Docker.

## Arquitectura del Sistema

El sistema está compuesto por:

- **Agentes Especializados**:
  - **Agente PGP** (puerto 8001): Genera Gherkin a partir de HUs usando LLM local (Llama via Ollama)
  - **Agente Clima** (puerto 8002): Responde consultas relacionadas con el clima (ejemplo)

- **Orquestador** (puerto 8003): 
  - Descubre agentes automáticamente
  - Detecta la habilidad requerida basándose en el contenido de la HU
  - Enruta la tarea al agente apropiado

- **API REST** (puerto 8000):
  - Recibe HU IDs de los clientes
  - Reenvía solicitudes al orquestador
  - Retorna la respuesta generada

## Inicio Rápido con Scripts Automáticos

### 🚀 Inicio Automático (Recomendado)

**Para PowerShell:**
```powershell
.\start-all.ps1
```

**Para CMD:**
```cmd
start-all.bat
```

**Para detener todos los servicios:**
```powershell
.\stop-all.ps1
```
```cmd
stop-all.bat
```

Estos scripts:
- ✅ Verifican que Python y pip estén instalados
- ✅ Crean y activan el entorno virtual automáticamente
- ✅ Instalan todas las dependencias
- ✅ Inician todos los servicios en segundo plano
- ✅ Muestran un resumen de URLs y comandos de prueba

---

## Ejecución Manual (Desarrollo)

1. **Clona el repositorio y entra al directorio del proyecto**
   ```bash
   git clone <repo-url>
   cd A2A-pgp-gherkin
   ```

2. **Crea y activa un entorno virtual**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Copia el archivo de variables de entorno**
   ```bash
   copy env.example .env
   ```

5. **Levanta los servicios en cuatro terminales diferentes:**

   - **Agente PGP**
     ```bash
     python agents/pgp_agent_service.py
     ```
   - **Agente Clima**
     ```bash
     python agents/clima_agent_service.py
     ```
   - **Orquestador**
     ```bash
     python core/orchestrator_service.py
     ```
   - **API REST**
     ```bash
     python core/api_rest_service.py
     ```

6. **Prueba el sistema**
   ```bash
   # Enviar HU ID para procesamiento
   curl -X POST http://localhost:8000/process-hu \
     -H "Content-Type: application/json" \
     -d '{"hu_id": "HU-001"}'
   ```

---

## Ejecución con Docker

1. **Construye y levanta los servicios**
   ```bash
   docker-compose up --build
   ```

2. **Prueba el sistema**
   ```bash
   # Enviar HU ID para procesamiento
   curl -X POST http://localhost:8000/process-hu \
     -H "Content-Type: application/json" \
     -d '{"hu_id": "HU-001"}'
   ```

3. **Verifica la salud de los servicios**
   - `GET http://localhost:8000/health` (API REST)
   - `GET http://localhost:8001/health` (Agente PGP)
   - `GET http://localhost:8002/health` (Agente Clima)
   - `GET http://localhost:8003/health` (Orquestador)

---

## Endpoints Disponibles

### API REST (puerto 8000)
- `POST /process-hu` - Procesa una HU por ID
- `GET /health` - Estado del servicio

### Agente PGP (puerto 8001)
- `POST /process` - Procesa HU y genera Gherkin
- `GET /.well-known/agent.json` - Información del agente
- `GET /health` - Estado del servicio

### Agente Clima (puerto 8002)
- `POST /process` - Responde consultas sobre clima
- `GET /.well-known/agent.json` - Información del agente
- `GET /health` - Estado del servicio

### Orquestador (puerto 8003)
- `POST /route-task` - Enruta tareas a agentes apropiados
- `GET /discover-agents` - Descubre agentes disponibles
- `GET /health` - Estado del servicio

---

## Variables de Entorno

Edita el archivo `.env` para cambiar las URLs de los servicios:

```env
# URLs para desarrollo local
AGENT_PGP_URL=http://localhost:8001
AGENT_CLIMA_URL=http://localhost:8002
ORCHESTRATOR_URL=http://localhost:8003
API_REST_URL=http://localhost:8000

# URLs para Docker
# AGENT_PGP_URL=http://pgp-agent:8001
# AGENT_CLIMA_URL=http://clima-agent:8002
# ORCHESTRATOR_URL=http://orchestrator:8003
# API_REST_URL=http://api-rest:8000
```

---

## Datos de Prueba

Los datos de prueba están en `data/test_cases.json` con las siguientes HUs disponibles:
- `HU-001`: Historia de usuario relacionada con PGP
- `HU-002`: Consulta sobre clima
- `HU-003`: Otra historia de usuario

---

## Características del Sistema

- **Descubrimiento Automático de Agentes**: Los agentes exponen su información via `/.well-known/agent.json`
- **Enrutamiento Inteligente**: El orquestador detecta automáticamente qué agente debe procesar cada HU
- **Arquitectura Desacoplada**: Cada componente puede ejecutarse independientemente
- **Soporte Multi-Agente**: Fácil agregar nuevos agentes especializados
- **LLM Local**: Integración con Ollama para procesamiento local
- **Docker Ready**: Configuración completa para contenedores

---

## Notas

- Los scripts automáticos son la forma más fácil de iniciar el sistema
- Puedes modificar los puertos en `docker-compose.yml` si es necesario
- El sistema detecta automáticamente si estás en desarrollo local o Docker
- Para agregar nuevos agentes, sigue el patrón de los agentes existentes