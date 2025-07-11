# start-all.ps1
Write-Host "   Iniciando todos los servicios de A2A-PGP-Gherkin..."
Write-Host ""

# Verificar si Python está instalado
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "   Error: Python no está instalado o no está en el PATH"
    Pause
    exit 1
}
Write-Host "   Python detectado"

# Verificar si el entorno virtual existe
if (-not (Test-Path "venv")) {
    Write-Host "   Error: No se encontró el entorno virtual 'venv'"
    Write-Host "   Crea el entorno virtual con: python -m venv venv"
    Write-Host "   Actívalo con: .\venv\Scripts\Activate.ps1"
    Write-Host "   Instala dependencias con: pip install -r requirements.txt"
    Pause
    exit 1
}

# Activar entorno virtual
Write-Host "   Activando entorno virtual..."
. .\venv\Scripts\Activate.ps1
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Error al activar el entorno virtual"
    Pause
    exit 1
}

Write-Host ""
Write-Host "Iniciando servicios en segundo plano..."
Write-Host ""

# Iniciar servicios en nuevas ventanas
Write-Host "Iniciando Agente PGP en puerto 8001..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", @'
Write-Host '
  AGENTE PGP
' -ForegroundColor Cyan
$host.UI.RawUI.WindowTitle = 'Agente PGP'; .\venv\Scripts\Activate.ps1; python -m agents.pgp_agent_service
'@

Write-Host "Iniciando Agente Clima en puerto 8002..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", @'
Write-Host '
  AGENTE CLIMA
' -ForegroundColor Yellow
$host.UI.RawUI.WindowTitle = 'Agente Clima'; .\venv\Scripts\Activate.ps1; python -m agents.clima_agent_service
'@

Write-Host "Iniciando Orquestador en puerto 8003..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", @'
Write-Host '
  ORQUESTADOR
' -ForegroundColor Green
$host.UI.RawUI.WindowTitle = 'Orquestador'; .\venv\Scripts\Activate.ps1; python -m core.orchestrator_service
'@

Write-Host "Iniciando API REST en puerto 8000..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", @'
Write-Host '
  API REST
' -ForegroundColor Magenta
$host.UI.RawUI.WindowTitle = 'API REST'; .\venv\Scripts\Activate.ps1; python -m api.rest_service
'@

Write-Host ""
Write-Host "   ¡Todos los servicios han sido iniciados!"
Write-Host ""
Write-Host "   Resumen de servicios:"
Write-Host "   • Agente PGP: http://localhost:8001"
Write-Host "   • Agente Clima: http://localhost:8002"
Write-Host "   • Orquestador: http://localhost:8003"
Write-Host "   • API REST: http://localhost:8000"
Write-Host ""
Write-Host "   Para probar el sistema:"
Write-Host "   • Enviar HU ID a: POST http://localhost:8000/process-hu"
Write-Host "   • Ejemplo: curl -X POST http://localhost:8000/process-hu -H `"Content-Type: application/json`" -d `"{`"hu_id`": `"HU-001`"}"
Write-Host ""
Write-Host "   Para detener todos los servicios, ejecuta: stop-all.ps1"
Write-Host ""
Write-Host "   Los servicios se ejecutan en ventanas separadas. Cierra las ventanas para detenerlos."
Write-Host ""
Pause 