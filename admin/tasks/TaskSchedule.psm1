<#
.SYNOPSIS
    Configuration for scheduled tasks.
#>

$TaskSchedule = @{

    RegionalKmzForFtp = @{
        Description = "Converts hosted feature layers to KMZ files and uploads KMZ files to ftp.wildfire.gov or ArcGIS Online."
        TaskPath = "\akwf\"
        ActionParams = @{
            Argument = "-File .\start.ps1 -WindowStyle Hidden -NonInteractive"
            Execute = "powershell.exe"
            WorkingDirectory = (Join-Path $Env:AKWF_ROOT "regional_kmz_for_ftp")
        }
        SettingsSetParams = @{
            AllowStartIfOnBatteries = $true
            DontStopIfGoingOnBatteries = $true
            ExecutionTimeLimit = (New-TimeSpan -Minutes 120)
            MultipleInstances = "IgnoreNew"
            RestartCount = 0
            WakeToRun = $true
        }
        TriggerParams = @{
            At = (Get-Date -Year 2025 -Month 07 -Day 09 -Hour 02 -Minute 00)
            Daily = $true
            DaysInterval = 1
        }
    }

    SatelliteImagePolling = @{
        Description = "Requests satellite images of fires from the Sentinel Hub Process API."
        TaskPath = "\akwf\"
        ActionParams = @{
            Argument = "-File .\start.ps1 -WindowStyle Hidden -NonInteractive"
            Execute = "powershell.exe"
            WorkingDirectory = (Join-Path $Env:AKWF_ROOT "satellite_image_polling")
        }
        SettingsSetParams = @{
            AllowStartIfOnBatteries = $true
            DontStopIfGoingOnBatteries = $true
            ExecutionTimeLimit = (New-TimeSpan -Minutes 30)
            MultipleInstances = "IgnoreNew"
            RestartCount = 3
            RestartInterval = (New-TimeSpan -Minutes 10)
            WakeToRun = $true
        }
        TriggerParams = @{
            At = (Get-Date -Year 2025 -Month 07 -Day 08 -Hour 18 -Minute 00)
            Daily = $true
            DaysInterval = 1
        }
    }
}

Export-ModuleMember -Variable TaskSchedule