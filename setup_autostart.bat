@echo off
echo ===================================
echo Setting up Fusion-Hybrid-V1 Autostart
echo ===================================

echo Creating startup script...
echo @echo off > "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\FusionHybrid.bat"
echo cd /d C:\Users\sschr\Desktop\server >> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\FusionHybrid.bat"
echo start /B python fusion_respond.py >> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\FusionHybrid.bat"
echo timeout /t 5 /nobreak ^> nul >> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\FusionHybrid.bat"
echo start /B python root_agent\web_ui\start_ui.py >> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\FusionHybrid.bat"

echo Creating Task Scheduler tasks...

schtasks /create /tn "FusionHybridBackend" /tr "C:\Users\sschr\Desktop\server\start_services.bat" /sc onstart /ru %USERNAME% /rl highest /f

echo ===================================
echo Autostart setup complete!
echo Services will start automatically on boot.
echo You can also run start_services.bat manually.
echo ===================================

pause 