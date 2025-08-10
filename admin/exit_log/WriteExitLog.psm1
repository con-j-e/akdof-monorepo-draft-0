function Write-ExitLog {
    param (
        [string]$ExitLog = (Join-Path $Env:AKDOF_ROOT "admin\exit_log\exit_log.csv"),

        [Parameter(Mandatory = $true)]
        [string]$ProjectName,

        [Parameter(Mandatory = $true)]
        [string]$ScriptName
    )

    $ExitCode = $LASTEXITCODE
    $Timestamp = [datetime]::UtcNow.ToString("o")
    $LogLine = "$Timestamp,$ProjectName,$ScriptName,$ExitCode`r`n"
    [System.IO.File]::AppendAllText($ExitLog, $LogLine)
}

Export-ModuleMember -Function Write-ExitLog