<#
.SYNOPSIS
    Configuration for scheduled tasks.
#>

$TaskSchedule = @{

    AkParcels = @{
        Description = "Updates the Alaska Statewide Parcels ArcGIS Online hosted feature layer."
        TaskPath = "\akdof\"
        ActionParams = @{
            Argument = "-File ./start.ps1 -WindowStyle Hidden -NonInteractive"
            Execute = "powershell.exe"
            WorkingDirectory = (Join-Path $Env:AKDOF_ROOT "projects/ak_parcels")
        }
        SettingsSetParams = @{
            AllowStartIfOnBatteries = $true
            DontStopIfGoingOnBatteries = $true
            ExecutionTimeLimit = (New-TimeSpan -Minutes 90)
            MultipleInstances = "IgnoreNew"
            RestartCount = 0
            WakeToRun = $true
        }
        TriggerParams = @{
            At = (Get-Date -Year 2025 -Month 09 -Day 13 -Hour 01 -Minute 00)
            Daily = $true
            DaysInterval = 1
        }
    }

    MedevacRunwaySearch = @{
        Description = "Updates a suite of ArcGIS Online hosted feature layers that drive core functionality of the Alaska Medevac Runway Search web app."
        TaskPath = "\akdof\"
        ActionParams = @{
            Argument = "-File ./start.ps1 -WindowStyle Hidden -NonInteractive"
            Execute = "powershell.exe"
            WorkingDirectory = (Join-Path $Env:AKDOF_ROOT "projects/medevac_runway_search")
        }
        SettingsSetParams = @{
            AllowStartIfOnBatteries = $true
            DontStopIfGoingOnBatteries = $true
            ExecutionTimeLimit = (New-TimeSpan -Minutes 30)
            MultipleInstances = "IgnoreNew"
            RestartCount = 0
            WakeToRun = $true
        }
        TriggerParams = @{
            At = (Get-Date -Year 2025 -Month 09 -Day 13 -Hour 02 -Minute 30)
            Daily = $true
            DaysInterval = 1
        }
    }

    RegionalKmzForFtp = @{
        Description = "Converts hosted feature layers to KMZ files and uploads KMZ files to ftp.wildfire.gov or ArcGIS Online."
        TaskPath = "\akdof\"
        ActionParams = @{
            Argument = "-File ./start.ps1 -WindowStyle Hidden -NonInteractive"
            Execute = "powershell.exe"
            WorkingDirectory = (Join-Path $Env:AKDOF_ROOT "projects/regional_kmz_for_ftp")
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
            At = (Get-Date -Year 2025 -Month 09 -Day 13 -Hour 03 -Minute 00)
            Daily = $true
            DaysInterval = 1
        }
    }
}

Export-ModuleMember -Variable TaskSchedule