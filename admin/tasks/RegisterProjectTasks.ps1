Import-Module (Join-Path $Env:AKDOF_ROOT "admin/tasks/TaskSchedule.psm1")

function Register-ProjectTasks {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$TaskSchedule,
        
        [switch]$OverwriteTasks
    )

    try {

        $Credential = Get-Credential
        $User = $Credential.UserName
        $PasswordBstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Credential.Password)
        $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($PasswordBstr)

        foreach ($TaskName in $TaskSchedule.Keys) {
            $TaskConfig = $TaskSchedule[$TaskName]

            $ExistingTask = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskConfig.TaskPath -ErrorAction SilentlyContinue
            if ($ExistingTask -and -not $OverwriteTasks) {
                Write-Warning "Task '$TaskName' already exists. Use the -OverwriteTasks switch to unregister and re-register existing tasks."
                continue
            }
            if ($ExistingTask -and $OverwriteTasks) {
                Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskConfig.TaskPath -Confirm:$false
                Write-Host "Unregistered existing task: $TaskName" -ForegroundColor Blue
            }

            $ActionParams = $TaskConfig.ActionParams
            $TaskAction = New-ScheduledTaskAction @ActionParams

            $SettingsSetParams = $TaskConfig.SettingsSetParams
            $TaskSettingsSet = New-ScheduledTaskSettingsSet @SettingsSetParams

            $TriggerParams = $TaskConfig.TriggerParams
            $TaskTrigger = New-ScheduledTaskTrigger @TriggerParams

            $RegistrationParams = @{
                Action = $TaskAction
                Description = $TaskConfig.Description
                Settings = $TaskSettingsSet
                TaskName = $TaskName
                TaskPath = $TaskConfig.TaskPath
                Trigger = $TaskTrigger
                User = $User
                Password = $Password
                RunLevel = "Highest"
            }
            
            Register-ScheduledTask @RegistrationParams | Out-Null
            Write-Host "Registered new task: $TaskName" -ForegroundColor Green
        }

    } finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($PasswordBstr)
        $Password = $null
    }
}

Register-ProjectTasks -TaskSchedule $TaskSchedule