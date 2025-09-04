↩️ [Back to repository overview](README.md)

# System
This repository and all documentation within assumes the use of a Windows Operating System that is connected to the State of Alaska network. Additionally, it assumes there is a user profile on the operating system with software installation capabilities, and that all work done in the repository will be done by the properly configured user profile.

The user profile is emphasized because in general we want to keep our development configuration separated from system-wide concerns.

# Software Tooling
Some of the software listed below can be considered optional, depending on the scope of work being done inside the repository. All of the listed software has been essential in the development and maintenance of the repository as a whole. PowerShell is not listed as software because the version used across this repository (PowerShell 5.1) is a core component of modern Windows operating systems.
| Tool      | Use Case |
|-----------------|-------------|
| [**ArcGIS Pro**](https://pro.arcgis.com/en/pro-app/latest/get-started/download-arcgis-pro.htm) | Projects that use ArcPy will require a licensed ArcGIS Pro installation to function. |
| [**GitHub CLI**](https://cli.github.com/) | Remote repository connection. |
| [**Git for Windows**](https://gitforwindows.org/) | Local version control system. |
| [**Miniconda**](https://www.anaconda.com/download/success) | A **user-level*** installation of Miniconda is required for all virtual environments and package management. |
| [**OpenSSL**](https://kb.firedaemon.com/support/solutions/articles/4000121705#Windows-Installer) | Retrieving broken SSL certificate chains. Further context [here](admin/certs/README.md). |
| [**VS Code**](https://code.visualstudio.com/Download) | VS Code may deliver a more consistent development experience than other IDEs / text editors (most work on this repository is done using VS Code). |

<sub>*The user-level Miniconda installation is particularly important on machines with a system-level ArcGIS Pro installation. We want our package management concerns to be separated from the ArcGIS Pro package manager and the user-level | system-level boundary helps achieve this seperation. See [example PowerShell profile](#example-profile) for further context.</sub>

# Getting Started
## Set Environment Variables
Two environment variables will be expected by PowerShell and Python scripts:

* **AKDOF_ROOT**: Directory path to the root of akdof-monorepo on the local file system, for example: *C:\REPOS\akdof-monorepo*.

* **AKDOF_USER**: Directory path to the root of the user profile which works on akdof-monorepo, for example: *C:\Users\Install*.

## Set PowerShell Execution Policy
Depending on current execution policy settings, you may need start a PowerShell session and manually enable script execution before any of the PowerShell scripts in the repository will work. 

### Example Command
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
<sub><sup>※</sup>Remote signed policy is a conservative choice (unsigned scripts from an external source, a remote repository for example, may be blocked).</sub>

### Additional Reading
* [About Execution Policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.5)
* [Get-ExecutionPolicy Command](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-executionpolicy?view=powershell-7.5)
* [Set-ExecutionPolicy Command](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy?view=powershell-7.5)

## Create PowerShell Profile
A user-level PowerShell profile handles the initial configuration that prepares us for calling `conda` commands in the terminal or from PowerShell scripts.

Your user-level PowerShell profile is expected to be in this exact location: *{AKDOF_USER}\Documents\PowerShell\Microsoft.PowerShell_profile.ps1*

### Example Profile
```
#---------------------------------------------------------------------------------------------------------------------------------#
# PERSONAL SETUP
#---------------------------------------------------------------------------------------------------------------------------------#

# place user path before machine path
# this way user level path settings will be prioritized if they conflict with system level path settings
# for example, a regular conda installation on the user path will execute commands instead of an arcgis pro conda installation on the system path
$Env:PATH = [Environment]::GetEnvironmentVariable("Path", "User") + ';' + [Environment]::GetEnvironmentVariable("Path", "Machine")

# custom console
function CustomizeConsole {
  $hostVersion="$($Host.Version.Major)`.$($Host.Version.Minor)"
  $Host.UI.RawUI.WindowTitle = "PowerShell $hostVersion  |  $Env:COMPUTERNAME  |  $Env:USERNAME"
}
CustomizeConsole

# welcome message
Write-Host "You have activated a user-level PowerShell profile"
Write-Host "Review the profile configuration here: $PROFILE"
Write-Host "---"
Set-Location $Env:AKDOF_ROOT

#-------------------------------------------------------------------------------------------------------------------------#
# CONDA SETUP 
#-------------------------------------------------------------------------------------------------------------------------#

# note that conda behavior in the shell session is determined in part by the user level config defined here: \miniconda3\.condarc

# tell conda to use a custom certificate chain for SSL verification
$Env:CONDA_SSL_VERIFY = (Join-Path $Env:AKDOF_ROOT "admin\certs\chain\anaconda.org_chain.pem")

# inside virtual conda environments, pip can have self-signed certificate errors doing pip installs
# so we tell pip to use a custom certificate chain for SSL verification as well
$Env:PIP_CERT = (Join-Path $Env:AKDOF_ROOT "admin\certs\chain\pypi.org_chain.pem")

# the expression below gets created by executing the `conda init powershell` command, and is initially saved to \Documents\WindowsPowerShell\profile.ps1
# here it has been modified to use the AKDOF_USER environment variable when looking for conda.exe
$CondaPath = (Join-Path $Env:AKDOF_USER "miniconda3\Scripts\conda.exe")
If (Test-Path $CondaPath) {
    (& $CondaPath "shell.powershell" "hook") | Out-String | ?{$_} | Invoke-Expression
}
```

### Additional Reading
* [About Profiles](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_profiles?view=powershell-7.5)

## Create .condarc
Preferred default behavior of `conda` commands is configured in a .condarc file.

Your user-level .condarc is expected to be in this exact location: *{AKDOF_USER}\miniconda3\\.condarc*

### Example .condarc
```
channels:
  - defaults

channel_priority: strict
show_channel_urls: true
auto_activate_base: false
auto_update_conda: false
```

### Additional Reading
* [Use Condarc](https://docs.conda.io/projects/conda/en/stable/user-guide/configuration/use-condarc.html#)

## Enable Long File System Paths (optional)
Depending on where akdof-monorepo is located in the local file system,
and whether projects use deeply nested folders and/or verbose folder and file naming,
issues with long file system paths may arise.

### Example Command
```
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```
<sub><sup>※</sup><i>You must run PowerShell as an administrator to execute this command.</i></sub>

### Additional Reading
* [Registry Setting to Enable Long Paths](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=powershell#registry-setting-to-enable-long-paths)


