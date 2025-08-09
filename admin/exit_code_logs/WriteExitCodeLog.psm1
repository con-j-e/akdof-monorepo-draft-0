function Write-ExitCodeLog {
    param (
        [string]$ExitCodeLog = (Join-Path $Env:AKDOF_ROOT "admin\logs\exit_codes.csv"),

        [Parameter(Mandatory = $true)]
        [string]$ProjectName,

        [Parameter(Mandatory = $true)]
        [string]$ScriptName
    )

    $ExitCode = $LASTEXITCODE
    $Timestamp = [datetime]::UtcNow.ToString("o")
    $LogLine = "$Timestamp,$ProjectName,$ScriptName,$ExitCode`r`n"
    [System.IO.File]::AppendAllText($ExitCodeLog, $LogLine)
}

Export-ModuleMember -Function Write-ExitCodeLog