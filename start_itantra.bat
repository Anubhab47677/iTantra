@echo off
echo ==========================================================================
echo                    iTANTRA UNIFIED DISASTER LAN LAUNCHER
echo Starting Python Multi-Protocol Server (ws://0.0.0.0:8765 and http://0.0.0.0:8081)
echo and Desktop Frontend Transceiver UI (http://localhost:8080)
echo ==========================================================================

cd /d "%~dp0itantra-ai-network\itantra-ai-network"
start "iTantra Python Relay Server" cmd /k "set PYTHONIOENCODING=utf-8 && set PYTHONPATH=protocol && python protocol/relay_server.py"

ping 127.0.0.1 -n 3 >nul

cd /d "C:\Users\Akansha Ajay\Desktop\itantrafrontend\itantrafrontend"
start "iTantra Desktop Frontend UI" cmd /k "npm run dev -- --host 0.0.0.0 --port 8080"

echo.
echo Both servers launched successfully across your Local Network (Wi-Fi / LAN)!
echo.
echo DEVICE 1 (Host Laptop): Open http://localhost:8080
echo DEVICE 2 (Second Phone / Laptop): Open http://192.168.X.X:8080 (Your IP)
echo ==========================================================================
ping 127.0.0.1 -n 2 >nul
