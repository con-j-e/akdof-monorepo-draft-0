↩️ [Back to repository overview](../../README.md)

↩️ [Back to admin](../README.md)

# About

[Windows Task Scheduler] orchestrates the scheduling and execution of automated tasks across the repository. Tasks are configured in a declarative manner using [TaskSchedule.psm1] and then registered with the operating system using [RegisterProjectTasks.ps1]. This approach has several advantages over manual task creation using the Task Scheduler GUI:
1. The complete task configuration for the repository can be viewed as one coherent schedule.
2. The complete task configuration becomes part of version control.
3. Details about what is currently being automated, and how/when it is automated, are observable to anyone that looks at the repository. 


# Configuring TaskSchedule.psm1

The task schedule is really just a hash map that declares parameters that will be be passed to task scheduling PowerShell functions. Viewing the established pattern for existing tasks in TaskSchedule.psm1, along with the relevant PowerShell documentation linked below, is the best way to become familiar with what TaskSchedule.psm1 is doing.

## PowerShell Documentation
* etc
* etc

# Executing RegisterProjectTasks.ps1

There are two quirks worth noting about this PowerShell script:
1. The script must be executed as administrator (scheduling tasks for the operating system always requires elevated privileges). 
2. At the time of writing this documentation (20250908) there is a [bug] that makes it impossible for the [PowerShell] application to execute the script successfully. [Windows Terminal] can be used to execute the script instead. 