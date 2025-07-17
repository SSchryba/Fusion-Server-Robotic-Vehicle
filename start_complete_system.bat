@echo off
echo ===================================
echo Starting Complete Fusion System
echo ===================================

cd /d "C:\Users\sschr\Desktop\server"

echo Starting Main Fusion Server...
start "Main Server" cmd /k "python main.py"

echo Waiting for main server...
timeout /t 3 /nobreak > nul

echo Starting Unified Control Center...
start "Control Center" cmd /k "cd unified_control_center && python control_server.py"

echo Waiting for control center...
timeout /t 3 /nobreak > nul

echo Starting Quantum Agent Integration...
start "Quantum Agent" cmd /k "python quantum_integration.py"

echo Waiting for quantum agent...
timeout /t 3 /nobreak > nul

echo Starting Root Agent Integration...
start "Root Agent" cmd /k "python root_agent_integration.py"

echo ===================================
echo All Systems Starting!
echo ===================================
echo Opening control interfaces...

timeout /t 5 /nobreak > nul

start "" "http://localhost:8000"
start "" "http://localhost:9000"

echo.
echo Fusion System: http://localhost:8000
echo Control Center: http://localhost:9000
echo Quantum Agent: Available
echo Root Agent: Available
echo.
echo Press any key to close...
pause > nul
