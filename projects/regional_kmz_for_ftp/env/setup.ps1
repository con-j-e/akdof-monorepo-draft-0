$WhichConda = Get-Command conda.exe
$CondaPath = $WhichConda.Path
$CondaVersion = & $CondaPath --version

$Response = Read-Host ("${CondaVersion} found at ${CondaPath}. Would you like to use this conda installation to conduct the environment setup? ( y / n )")
if (-not ($Response -match '^[Yy]$')) {
    Write-Host "Aborted by user."
    exit
}
$Response = Read-Host ("This setup script is executing from the directory ${PSScriptRoot}. Would you like to setup the environment in this location? ( y / n )")
if (-not ($Response -match '^[Yy]$')) {
    Write-Host "Aborted by user."
    exit
}

Set-Location $PSScriptRoot
Write-Host "Beginning setup..."

# When configuring an environment that integrates with arcpy, we override our .condarc channel preferences:
# Check the esri channel for packages before checking conda-forge,
# and use a 'flexible' channel priority instead of 'strict'.
$env:CONDA_CHANNELS = "esri,conda-forge"
$env:CONDA_CHANNEL_PRIORITY = "flexible"

# Instead building the environment from a YAML file,
# we build the arcpy-base environment and then install packages manually.
& conda create --prefix=./conda_env -c esri arcpy-base=3.5
& conda activate ./conda_env

if ($env:CONDA_DEFAULT_ENV) {
    $Response = Read-Host ("Conda environment '$($env:CONDA_DEFAULT_ENV)' is now active. Would you like the setup script to proceed with the activated environment? ( y / n )")
} else {
    Write-Host "Unable to activate conda environment. Shell profile may require 'conda init' before this setup script will work as expected. Exiting..."
    exit
}
if (-not ($Response -match '^[Yy]$')) {
    Write-Host "Aborted by user."
    exit
}

# The akdof_shared package has dependencies that we pre-emptively get from conda channels, to minimize pip installs.
& conda install --freeze-installed `
    aiodns `
    aiohttp `
    argon2-cffi `
    geopandas `
    jaraco.classes `
    keyring `
    more-itertools `
    pycryptodome `
    pydantic

# pyogrio dependencies will attempt to modify packages that are native to the arcpy-base environment.
# As a matter of precaution we do not want to modify arcpy-base in any way.
# The regional_kmz_for_ftp project uses arcpy for all spatial data processing, so pyogrio dependencies can safely be left out.
# This is an atypical environment configuration, and used in other contexts could lead to import errors and/or unexpected behavior.
& conda install pyogrio --no-deps

& conda install -c esri geomet=1.0.0
& pip install -e (Join-Path $Env:AKDOF_ROOT "library/akdof_shared")

Write-Host "Conda environment '$($env:CONDA_DEFAULT_ENV)' setup complete. Exiting..."
& conda deactivate
exit