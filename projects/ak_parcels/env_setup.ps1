$WhichConda = Get-Command conda.exe
$CondaPath = $WhichConda.Path
$CondaVersion = & $CondaPath --version

$Response = Read-Host ("${CondaVersion} found at ${CondaPath}. Would you like to use this conda installation to conduct the environment setup? ( y / n )")
if (-not ($response -match '^[Yy]$')) {
    Write-Host "Aborted by user."
    exit
}
$Response = Read-Host ("This setup script is executing from the directory ${PSScriptRoot}. Would you like to setup the environment in this location? ( y / n )")
if (-not ($response -match '^[Yy]$')) {
    Write-Host "Aborted by user."
    exit
}

Set-Location $PSScriptRoot
Write-Host "Beginning setup..."

& conda env create --prefix .\conda_env -f .\environment.yml
& conda activate .\conda_env
if ($env:CONDA_DEFAULT_ENV) {
    $Response = Read-Host ("Conda environment '$($env:CONDA_DEFAULT_ENV)' is now active. Would you like the setup script to proceed with the activated environment? ( y / n )")
} else {
    Write-Host "Unable to activate conda environment. Shell profile may require 'conda init' before this setup script will work as expected. Exiting..."
    exit
}
if (-not ($response -match '^[Yy]$')) {
    Write-Host "Aborted by user."
    exit
}
& conda install -c esri geomet=1.0.0

$Library = Join-Path $Env:AKDOF_ROOT "library"
& pip install -e (Join-Path $Library "akwf_gis")
& pip install -e (Join-Path $Library "akwf_io")
& pip install -e (Join-Path $Library "akwf_models")
& pip install -e (Join-Path $Library "akwf_security")
& pip install -e (Join-Path $Library "akwf_utils")

Write-Host "Conda environment '$($env:CONDA_DEFAULT_ENV)' setup complete. Exiting..."
& conda deactivate
exit