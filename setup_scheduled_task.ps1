# 股票监控定时任务安装脚本
# 以管理员身份运行

$ErrorActionPreference = "Stop"
$taskName = "StockMonitorCheck"

# 删除旧任务
try { schtasks /delete /tn $taskName /f 2>&1 | Out-Null } catch {}

$xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2026-05-10T00:00:00</Date>
    <Author>StockMonitor</Author>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-05-11T14:30:00</StartBoundary>
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
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>D:\Claude\stock_monitor\run_monitor.bat</Command>
    </Exec>
  </Actions>
</Task>
"@

$xmlPath = "D:\Claude\stock_monitor\task_schedule.xml"
[System.IO.File]::WriteAllText($xmlPath, $xml, [System.Text.Encoding]::Unicode)

schtasks /create /tn $taskName /xml $xmlPath /f

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================"
    Write-Host " 定时任务创建完成！"
    Write-Host " 任务名称: $taskName"
    Write-Host " 运行时间: 交易日 14:30 每天一次"
    Write-Host "============================================"
    Write-Host ""
    Write-Host "管理命令："
    Write-Host "  查看状态: schtasks /query /tn $taskName /fo LIST /v"
    Write-Host "  手动运行: D:\Claude\stock_monitor\run_monitor.bat"
    Write-Host "  删除任务: schtasks /delete /tn $taskName /f"
} else {
    Write-Host "创建失败，请用管理员权限运行此脚本"
}
