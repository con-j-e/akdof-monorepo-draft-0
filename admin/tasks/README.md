↩️ [Back to repository overview](../../README.md)

↩️ [Back to admin](../README.md)

# About

[Windows Task Scheduler](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page) orchestrates the scheduling and execution of automated tasks across the repository. Tasks are configured in a declarative manner using [TaskSchedule.psm1](TaskSchedule.psm1) and then registered with the operating system using [RegisterProjectTasks.ps1](RegisterProjectTasks.ps1). This approach has several advantages over manual task creation using the Task Scheduler GUI:
1. The complete task configuration for the repository can be viewed as one coherent schedule.
2. The complete task configuration becomes part of version control.
3. Details about what is currently being automated, and how/when it is automated, are observable to anyone that looks at the remote repository. 

# Configuring TaskSchedule.psm1

The task schedule is really just a nested [hash table](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_hash_tables?view=powershell-7.5) of parameters that will be be passed to core task scheduling PowerShell functions by [Register-ProjectTasks](RegisterProjectTasks.ps1#L3).

```
# 
$TaskSchedule = @{

    # entries in the task schedule are keyed by task names
    # when applicable, the task name should be a PascalCase rendition of the project root directory that contains the script being run
    AkParcels = @{

        # a concise overview of what this task does
        Description = "Updates the Alaska Statewide Parcels ArcGIS Online hosted feature layer."

        # task path should be the same for all tasks in the task schedule
        # this keeps our tasks organized in a single custom "directory" when viewed in the Task Scheduler GUI
        TaskPath = "\akdof\"

        # parameter configuration for 
        ActionParams = @{
            Argument = "-File .\start.ps1 -WindowStyle Hidden -NonInteractive"
            Execute = "powershell.exe"
            WorkingDirectory = (Join-Path $Env:AKDOF_ROOT "projects\ak_parcels")
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
            At = (Get-Date -Year 2025 -Month 09 -Day 03 -Hour 01 -Minute 00)
            Daily = $true
            DaysInterval = 1
        }
    }
}
```

# Executing RegisterProjectTasks.ps1

There are two quirks worth noting about this PowerShell script:
1. The script must be executed as administrator (scheduling tasks requires elevated privileges) 
2. At the time of writing this documentation (September of 2025) there is a [bug in PowerShell 5.1](https://superuser.com/questions/1885304/powershell-exe-does-not-prompt-for-credentials) that makes it impossible for the [PoweShell command line shell](https://learn.microsoft.com/en-us/powershell/scripting/overview?view=powershell-7.5#command-line-shell) to execute the script successfully. [Windows Terminal](https://learn.microsoft.com/en-us/windows/terminal/) can be used to execute the script instead.  