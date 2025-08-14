Import-Module (Join-Path $Env:AKDOF_ROOT "admin\exit_log\WriteExitLog.psm1")

$ScriptRoot = Get-Item $PSScriptRoot
$CondaPyExe = Join-Path $ScriptRoot "\conda_env\python.exe"
$MainPy = Join-Path $ScriptRoot "main.py"

$PSDefaultParameterValues['Out-File:Width'] = 5000
& $CondaPyExe $MainPy 2>> (Join-Path $ScriptRoot "stderr.txt")
Write-ExitLog -ProjectName $ScriptRoot.Name -ScriptName "main"

exit