@echo off
title Tao Public URL cho Chiikawa Claw Machine
cd /d "%~dp0"
echo ======================================================================
echo    CHIIKAWA CLAW MACHINE - TAO PUBLIC URL (INTERNET REALTIME)
echo ======================================================================
echo.
echo Dang mo duong truyen cong khai (Public Tunnel) toi port 5000...
echo Sau vai giay, ban se nhan duoc mot PUBLIC URL (vi du: https://xxxx.pinggy.link)
echo Ban co the gui URL do cho ban be de choi cung nhau qua Internet!
echo.
echo (Nhan Ctrl+C neu muon dung lai)
echo ======================================================================
ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:5000 a.pinggy.io
pause
