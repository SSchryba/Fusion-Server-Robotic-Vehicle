@echo off
echo ===================================
echo Fixing and Testing Fusion-Hybrid-V1
echo ===================================

cd /d C:\Users\sschr\Desktop\server

echo Killing existing processes...
taskkill /F /IM python.exe 2>nul

echo Installing ALL dependencies...
pip install rich schedule requests numpy pandas fastapi uvicorn pydantic aiofiles python-multipart jinja2 python-dotenv flask werkzeug

echo Creating ALL required directories...
mkdir logs 2>nul
mkdir root_agent\web_ui\logs 2>nul
mkdir test_output 2>nul
mkdir models\hybrid_models 2>nul
mkdir tools\installed 2>nul

echo Creating required files...
type nul > root_agent\web_ui\logs\aiagent.log
type nul > tools\tools_log.json
echo {} > tools\tools_log.json

echo Starting Backend Server...
start /B python fusion_respond.py

echo Waiting for backend...
timeout /t 10 /nobreak

echo Starting UI Server...
start /B python root_agent\web_ui\start_ui.py

echo Waiting for UI...
timeout /t 10 /nobreak

echo Running comprehensive health check...
python tests\api_and_ui_healthcheck.py

echo ===================================
echo Testing chat functionality...
echo ===================================
curl -X POST http://localhost:8000/fusion/respond -H "Content-Type: application/json" -d "{\"prompt\": \"Hello, are you working?\"}"

echo.
echo ===================================
echo Services should now be running:
echo Backend: http://localhost:8000/docs
echo UI: http://localhost:5000
echo ===================================

pause 