# Flujo Técnico del Proyecto: A2A PGP Gherkin

Este documento describe el flujo técnico del sistema, desde que se realiza una consulta (por Postman o frontend) hasta que se obtiene la respuesta final.

---

## 1. Consulta inicial

El usuario (o Postman, o el frontend) envía una petición HTTP POST a:

```
http://localhost:8000/api/generate-pgp
```

con un JSON como:

```json
{
  "hu_id": "HU-123"
}
```

---

## 2. API REST recibe la solicitud

- El servicio **api-rest** (FastAPI, puerto 8000) recibe la petición en el endpoint `/api/generate-pgp`.
- Extrae el `hu_id` del cuerpo de la petición.
- Llama al orquestador enviando una petición POST a:

```
http://localhost:8003/route-hu
```

con el mismo JSON.

---

## 3. Orquestador procesa la HU

- El servicio **orchestrator** (FastAPI, puerto 8003) recibe la petición en `/route-hu`.
- Busca la HU en el archivo `data/test_cases.json` usando el `hu_id`.
- Analiza el texto de la HU para determinar a qué agente debe enviarla (por ejemplo, si es de tipo PGP o Clima).
- Consulta los agentes registrados (por ejemplo, `agente-pgp` y `agente-clima`) para ver cuál tiene la skill adecuada.
- Reenvía la HU al agente correspondiente mediante una petición POST a:
  - `http://localhost:8001/process-hu` (para PGP)
  - `http://localhost:8002/process-hu` (para Clima)

---

## 4. Agente PGP procesa la HU

- El servicio **agente-pgp** (FastAPI, puerto 8001) recibe la petición en `/process-hu`.
- Si la HU es de tipo PGP:
  - Prepara el prompt para el LLM (Ollama).
  - Llama al modelo LLM local (Ollama) usando la librería LangChain y el endpoint:
    - `http://localhost:11434`
  - El LLM genera el contenido en formato Gherkin.
  - Si Ollama falla, usa el método clásico para generar el Gherkin.

---

## 5. Respuesta del agente

- El agente PGP responde al orquestador con el resultado (`status`, `hu_id`, `gherkin_content`, `message`).

---

## 6. Orquestador reenvía la respuesta

- El orquestador recibe la respuesta del agente y la reenvía a la API REST.

---

## 7. API REST responde al usuario

- La API REST recibe la respuesta del orquestador y la devuelve al usuario (Postman o frontend) en formato JSON.

---

## Resumen visual del flujo

```
Usuario/Postman
   ↓
API REST (/api/generate-pgp)
   ↓
Orquestador (/route-hu)
   ↓
Agente PGP (/process-hu)
   ↓
Ollama (LLM local)
   ↓
Agente PGP → Orquestador → API REST → Usuario
``` 