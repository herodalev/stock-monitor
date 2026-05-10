@echo off
chcp 65001 >nul
cd /d "%~dp0"

set SCRIPT_PATH=%~dp0run_monitor.bat
set TASK_NAME=StockMonitorCheck
set PYTHON_PATH=C:\Users\大侠\AppData\Local\Programs\Python\Python312\python.exe

echo ========================================
echo   股票监控 - Windows 任务计划设置
echo ========================================
echo.
echo 1. 创建定时任务（交易时段每30分钟运行）
echo 2. 删除定时任务
echo 3. 手动运行一次
echo 4. 查看任务状态
echo.

set /p CHOICE=请选择 (1/2/3/4):

if "%CHOICE%"=="1" goto create
if "%CHOICE%"=="2" goto delete
if "%CHOICE%"=="3" goto runnow
if "%CHOICE%"=="4" goto status
goto end

:create
echo.
echo 正在创建定时任务...
echo 任务将在每个交易日 9:30-15:00 期间每30分钟运行一次

schtasks /create /tn "%TASK_NAME%" /tr "'%SCRIPT_PATH%'" /sc MINUTE /mo 30 /sd 2026/01/01 /ed 2027/12/31 /f

echo.
echo 创建完成！可在"任务计划程序"中查看和管理
echo 任务名称: %TASK_NAME%
goto end

:delete
schtasks /delete /tn "%TASK_NAME%" /f
echo 任务已删除
goto end

:runnow
echo 正在手动运行监控...
call "%SCRIPT_PATH%"
goto end

:status
schtasks /query /tn "%TASK_NAME%" /fo LIST /v 2>nul
if errorlevel 1 echo 任务不存在
goto end

:end
pause
