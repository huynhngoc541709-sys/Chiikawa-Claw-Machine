@echo off
title Chiikawa Claw Machine Server
cd /d "%~dp0"
echo ========================================================
echo   CHIIKAWA CLAW MACHINE - MAY GAP THU ONLINE
echo ========================================================
echo Dang khoi dong may chu Socket.IO...
python server.py
pause
