@echo off
echo.
echo ====================================================
echo 🚀 Fusion-Hybrid-V1 Control UI Startup
echo ====================================================
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ❌ Error: main.py not found. Make sure you're in the correct directory.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo ⚠️ Warning: Virtual environment not found. Creating one...
    python -m venv .venv
    echo ✅ Virtual environment created.
    echo.
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing/updating dependencies...
pip install fastapi uvicorn websockets psutil

echo.
echo ====================================================
echo 🌟 Starting Fusion-Hybrid-V1 Control UI
echo ====================================================
echo.
echo 📡 Server will start on: http://localhost:9000
echo 📊 Dashboard URL: http://localhost:9000
echo 🔌 WebSocket URL: ws://localhost:9000/ws
echo ❤️ Health Check: http://localhost:9000/health
echo.
echo Press Ctrl+C to stop the server
echo ====================================================
echo.

REM Start the server
python main.py

pause 