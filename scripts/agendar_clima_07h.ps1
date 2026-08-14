# Agendar disparo diario as 07:00 (Windows Task Scheduler)
# Execute no PowerShell:

$Projeto = Split-Path $PSScriptRoot -Parent
$Bat = Join-Path $PSScriptRoot "disparo_clima_07h.bat"
$Acao = New-ScheduledTaskAction -Execute $Bat -WorkingDirectory $Projeto
$Gatilho = New-ScheduledTaskTrigger -Daily -At "07:00"
$Config = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "RuralPro Clima WhatsApp 07h" -Action $Acao -Trigger $Gatilho -Settings $Config -Description "Abre wa.me com card de clima para inscritos WhatsApp"

Write-Host "Tarefa agendada: RuralPro Clima WhatsApp 07h (todos os dias as 07:00)"
