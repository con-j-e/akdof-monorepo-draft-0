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
Write-Host "Or by running ``code `$PROFILE``"
Write-Host "---"
Set-Location $Env:AKDOF_ROOT

#-------------------------------------------------------------------------------------------------------------------------#
# CONDA SETUP 
#-------------------------------------------------------------------------------------------------------------------------#

# note that conda behavior in the shell session is determined in part by the user level config defined here: ..\miniconda3\.condarc

# tell conda to use a custom certificate chain for SSL verification
$Env:CONDA_SSL_VERIFY = (Join-Path $Env:AKDOF_ROOT "admin\certs\chain\anaconda.org_chain.pem")

# inside virtual conda environments, pip can have self-signed certificate errors doing pip installs
# so we tell pip to use a custom certificate chain for SSL verification as well
$Env:PIP_CERT = (Join-Path $Env:AKDOF_ROOT "admin\certs\chain\pypi.org_chain.pem")

# the expression below gets created by executing the `conda init powershell` command, and is initially saved to ..\Documents\WindowsPowerShell\profile.ps1
# here it has been modified to use the AKDOF_USER environment variable when looking for conda.exe
$CondaPath = (Join-Path $Env:AKDOF_USER "miniconda3\Scripts\conda.exe")
If (Test-Path $CondaPath) {
    (& $CondaPath "shell.powershell\hook") | Out-String | ?{$_} | Invoke-Expression
}