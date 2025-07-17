@echo off
echo ===================================
echo Starting Fusion-Hybrid-V1 Services
echo ===================================

cd /d C:\Users\sschr\Desktop\server

echo Installing dependencies...
pip install rich schedule requests numpy pandas fastapi uvicorn pydantic aiofiles python-multipart jinja2 python-dotenv

echo Creating log directories...
if not exist "logs" mkdir logs
if not exist "root_agent\web_ui\logs" mkdir root_agent\web_ui\logs
if not exist "test_output" mkdir test_output
if not exist "models\hybrid_models" mkdir models\hybrid_models

echo Creating log files...
echo. > root_agent\web_ui\logs\aiagent.log

echo Starting Backend Server...
start /B python fusion_respond.py > logs\backend.log 2>&1

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting UI Server...
start /B python root_agent\web_ui\start_ui.py > logs\ui.log 2>&1

echo ===================================
echo Services Started!
echo Backend: http://localhost:8000
echo UI: http://localhost:5000
echo ===================================

echo Running health check...
timeout /t 5 /nobreak > nul
python tests\api_and_ui_healthcheck.py

pause 