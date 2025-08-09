# enable long file system paths (to allow for deep folder structure and/or verbose folder and file naming)
## you must run PowerShell as an administrator to execute this command
### https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# enable PowerShell script execution (PowerShell is used for various system level tasks across the monorepo)
## this command may need to be entered manually in a PowerShell session before any PowerShell script execution is possible
## remote signed policy is a conservative choice (unsigned scripts from an external source, a remote repository for example, may be blocked)
### https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.5
### https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-executionpolicy?view=powershell-7.5
### https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy?view=powershell-7.5
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# set required environment variables for user and monorepo root paths
### https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-7.5
[Environment]::SetEnvironmentVariable("AKDOF_USER", "C:\Users\Install", "User")
[Environment]::SetEnvironmentVariable("AKDOF_ROOT", "C:\REPOS\con-j-e\akdof-monorepo", "User")