@echo off
chcp 65001 > nul
title Happ / VLESS Google GeoIP Checker
cd /d "%~dp0"
python check_nodes.py %*
echo.
pause
