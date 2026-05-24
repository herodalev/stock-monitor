# 股票监控定时任务 — 北京时间 11:00 和 14:30，周一至周五
# 以管理员身份运行

$ErrorActionPreference = "Stop"
$taskName = "StockMonitorCheck"
$pythonPath = "C:\Users\大侠\AppData\Local\Programs\Python\Python312\python.exe"
$monitorDir = "D:\Claude\stock_monitor"

# 删除旧任务
try { schtasks /delete /tn $taskName /f 2>&1 | Out-Null } catch {}

$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2026-05-24T00:00:00</Date>
    <Author>StockMonitor</Author>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-05-25T11:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek>
          <Monday/>
          <Tuesday/>
          <Wednesday/>
          <Thursday/>
          <Friday/>
        </DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
    <CalendarTrigger>
      <StartBoundary>2026-05-25T14:30:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek>
          <Monday/>
          <Tuesday/>
          <Wednesday/>
          <Thursday/>
          <Friday/>
        </DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Enabled>true</Enabled>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$pythonPath</Command>
      <Arguments>monitor.py</Arguments>
      <WorkingDirectory>$monitorDir</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

$xmlPath = "$monitorDir\task_schedule.xml"
[System.IO.File]::WriteAllText($xmlPath, $xml, [System.Text.Encoding]::Unicode)

schtasks /create /tn $taskName /xml $xmlPath /f

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================"
    Write-Host " 定时任务创建完成！"
    Write-Host " 任务名称: $taskName"
    Write-Host " 运行时间: 交易日 11:00 + 14:30 (北京时间)"
    Write-Host "============================================"
    Write-Host ""
    Write-Host "管理命令："
    Write-Host "  查看状态: schtasks /query /tn $taskName /fo LIST /v"
    Write-Host "  手动运行: python $monitorDir\monitor.py"
    Write-Host "  删除任务: schtasks /delete /tn $taskName /f"
} else {
    Write-Host "创建失败，请用管理员权限运行此脚本"
}
