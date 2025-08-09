Import-Module (Join-Path $Env:AKWF_ROOT "lib\ps\PyScriptUtils.psm1")

$ScriptRoot = Get-Item $PSScriptRoot
$CondaPyExe = Join-Path $ScriptRoot "\conda_env\python.exe"
$MainPy = Join-Path $ScriptRoot "main.py"

$ExitCodeLog = Join-Path $Env:AKWF_ROOT "status_codes.csv"
$PSDefaultParameterValues['Out-File:Width'] = 5000
& $CondaPyExe $MainPy 2>> (Join-Path $ScriptRoot "stderr.txt")
Write-ExitCodeLog -ExitCodeLog $ExitCodeLog -ProjectName $ScriptRoot.Name -ScriptName "main"
exit