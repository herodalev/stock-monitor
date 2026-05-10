@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
"C:\Users\大侠\AppData\Local\Programs\Python\Python312\python.exe" monitor.py >> monitor_log.txt 2>&1
