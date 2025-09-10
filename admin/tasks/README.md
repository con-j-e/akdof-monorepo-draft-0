↩️ [Back to repository overview](../../README.md)

↩️ [Back to admin](../README.md)

# About

[Windows Task Scheduler](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page) orchestrates the scheduling and execution of automated tasks across the repository. Tasks are configured in a declarative manner using [TaskSchedule.psm1](TaskSchedule.psm1) and then registered with the operating system using [RegisterProjectTasks.ps1](RegisterProjectTasks.ps1). This approach has several advantages over manual task creation using the Task Scheduler GUI:
1. The complete task configuration for the repository can be viewed as one coherent schedule.
2. The complete task configuration becomes part of version control.
3. Details about what is currently being automated, and how/when it is automated, are observable to anyone that looks at the remote repository. 

# Configuring TaskSchedule.psm1

The task schedule is really just a [hash table](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_hash_tables?view=powershell-7.5) of parameters that will be be passed to core task scheduling PowerShell functions by [Register-ProjectTasks](). 

# Executing RegisterProjectTasks.ps1

There are two quirks worth noting about this PowerShell script:
1. The script must be executed as administrator (scheduling tasks requires elevated privileges) 
2. At the time of writing this documentation (September of 2025) there is a [bug in PowerShell 5.1](https://superuser.com/questions/1885304/powershell-exe-does-not-prompt-for-credentials) that makes it impossible for the [PoweShell command line shell](https://learn.microsoft.com/en-us/powershell/scripting/overview?view=powershell-7.5#command-line-shell) to execute the script successfully. [Windows Terminal](https://learn.microsoft.com/en-us/windows/terminal/) can be used to execute the script instead.  