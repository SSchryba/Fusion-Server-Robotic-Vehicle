@echo off
REM Enhanced AI Training Server - 24/7 Multi-Model Training (Windows Version)
setlocal enabledelayedexpansion

REM Configuration
set "PROJECT_DIR=%USERPROFILE%\faith-server"
set "VENV_DIR=%PROJECT_DIR%\venv"
set "SERVER_DIR=%PROJECT_DIR%\server"
set "LOGS_DIR=%PROJECT_DIR%\logs"
set "MODELS_DIR=%PROJECT_DIR%\models"
set "DATA_DIR=%PROJECT_DIR%\training_data"
set "CONFIG_DIR=%PROJECT_DIR%\config"

REM Resource limits and monitoring
set "MAX_MEMORY_USAGE=80"
set "MAX_GPU_USAGE=95"
set "MIN_DISK_SPACE=10"

REM Create log function
call :log "=== Starting Enhanced AI Training Server ==="

REM Create necessary directories
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    call :log "Creating virtual environment..."
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        call :log "ERROR: Failed to create virtual environment"
        exit /b 1
    )
)

REM Activate virtual environment
call :log "Activating virtual environment..."
call "%VENV_DIR%\Scripts\activate.bat"

REM Install/upgrade requirements
call :log "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    call :log "WARNING: Some packages failed to install"
)

REM Install Ollama if not present
where ollama >nul 2>nul
if errorlevel 1 (
    call :log "Ollama not found. Please install Ollama from https://ollama.ai/"
    pause
    exit /b 1
)

REM Start Ollama daemon
call :log "Starting Ollama daemon..."
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if errorlevel 1 (
    start /B ollama serve > "%LOGS_DIR%\ollama.log" 2>&1
    timeout /t 5 /nobreak >nul
    call :log "Ollama daemon started"
) else (
    call :log "Ollama daemon already running"
)

REM Check if Ollama is responding
curl -s http://localhost:11434/api/version >nul 2>&1
if errorlevel 1 (
    call :log "ERROR: Ollama daemon not responding"
    exit /b 1
)

REM Pull essential models (subset for initial setup)
call :log "Pulling essential models..."
call :pull_model "llama2:latest"
call :pull_model "mistral:latest"
call :pull_model "codellama:latest"
call :pull_model "gemma:2b"

REM Start background monitoring
call :log "Starting monitoring service..."
start /B cmd /c "call :monitoring_loop"

REM Start FastAPI server
call :log "Starting FastAPI training server..."
cd /d "%SERVER_DIR%"
start /B uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --access-log --log-file "%LOGS_DIR%\api_server.log"

REM Main server loop
call :log "AI Training Server is now running 24/7"
call :log "Monitor logs in: %LOGS_DIR%"
call :log "API endpoint: http://localhost:8000"
call :log "Ollama endpoint: http://localhost:11434"
call :log "Press Ctrl+C to stop the server"

:main_loop
timeout /t 3600 /nobreak >nul
call :log "Server heartbeat - %date% %time%"
goto main_loop

REM Functions
:log
echo [%date% %time%] %~1
echo [%date% %time%] %~1 >> "%LOGS_DIR%\training_server.log"
goto :eof

:pull_model
call :log "Pulling model: %~1"
ollama pull %~1
if errorlevel 1 (
    call :log "Failed to pull model: %~1"
)
goto :eof

:check_resources
REM Simple resource check - Windows version
for /f "tokens=2 delims= " %%i in ('wmic OS get TotalVisibleMemorySize /value ^| find "="') do set total_mem=%%i
for /f "tokens=2 delims= " %%i in ('wmic OS get FreePhysicalMemory /value ^| find "="') do set free_mem=%%i
set /a mem_usage=100*(total_mem-free_mem)/total_mem

if %mem_usage% GTR %MAX_MEMORY_USAGE% (
    call :log "WARNING: Memory usage at %mem_usage%% - pausing new training jobs"
    exit /b 1
)
exit /b 0

:monitoring_loop
call :log "Starting monitoring service..."
:monitor_loop
timeout /t 60 /nobreak >nul

REM Get system metrics
for /f "tokens=2 delims= " %%i in ('wmic cpu get loadpercentage /value ^| find "="') do set cpu_usage=%%i
call :check_resources
set mem_result=%errorlevel%

REM Check if Ollama is still running
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if errorlevel 1 (
    call :log "Ollama daemon died - restarting..."
    start /B ollama serve > "%LOGS_DIR%\ollama.log" 2>&1
)

REM Log metrics
if %mem_result% EQU 0 (
    call :log "METRICS: CPU=%cpu_usage%%"
) else (
    call :log "METRICS: CPU=%cpu_usage%% - High memory usage detected"
)

goto monitor_loop

REM Cleanup on exit
:cleanup
call :log "Shutting down AI training server..."
taskkill /F /IM ollama.exe >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq uvicorn*" >nul 2>&1
call :log "Cleanup completed"
goto :eof 