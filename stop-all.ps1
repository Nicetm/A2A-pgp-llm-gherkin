# stop-all.ps1
Write-Host "   Deteniendo todos los servicios de A2A-PGP-Gherkin..."
Write-Host ""

# Detener procesos de Python que ejecutan los servicios
Write-Host "   Deteniendo procesos de Python..."
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force
    Write-Host "   Procesos de Python detenidos"
} else {
    Write-Host "   No se encontraron procesos de Python ejecutándose"
}

Write-Host ""
Write-Host "   Verificando puertos en uso..."

foreach ($port in 8000,8001,8002,8003) {
    Write-Host "   Verificando puerto $port..."
    $connections = netstat -ano | Select-String ":$port\s"
    foreach ($conn in $connections) {
        $parts = $conn -split "\s+"
        $procId = $parts[-1]
        if ($procId -match '^\d+$') {
            try {
                Stop-Process -Id $procId -Force -ErrorAction Stop
                Write-Host "   Proceso $procId detenido en puerto $port"
            } catch {
                Write-Host "   Error al detener proceso $procId"
            }
        }
    }
}

Write-Host ""
Write-Host "   Limpiando archivos temporales..."

# Limpiar __pycache__ en el directorio raíz y subdirectorios
$pycacheDirs = Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
foreach ($dir in $pycacheDirs) {
    Remove-Item -Recurse -Force $dir.FullName
    Write-Host "   $($dir.FullName) eliminado"
}

Write-Host ""
Write-Host "   Todos los servicios han sido detenidos y limpiados"
Write-Host ""
Write-Host "   Para reiniciar todos los servicios, ejecuta: start-all.ps1"
Write-Host ""
Pause 