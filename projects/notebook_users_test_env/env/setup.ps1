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

# Instead building the environment from a YAML file,
# we build the arcgis (ArcGIS API for Python) environment and then install packages manually.
& conda create --prefix=./conda_env -c esri arcgis
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

# Getting geopandas from the esri channel because their version
# does not use pyogrio (pyogrio has conflicts with the ArcGIS API for Python).
& conda install -c esri geopandas

# People on our team like to use notebooks during development.
# Prior experience suggests that ipykernel along with having the Jupyter extension
# in VS Code is a minimum requirement for .ipynb functionality in VS Code.
& conda install ipykernel

# The akdof_shared package has dependencies that we pre-emptively get from conda channels, to minimize pip installs.
& conda install `
    aiodns `
    aiohttp `
    argon2-cffi `
    jaraco.classes `
    more-itertools `
    pycryptodome

# If pyogrio is not installed, pip will attempt to install it with akdof_shared.
# But pyogrio dependencies will attempt to modify packages that are native to the ArcGIS API for Python, and
# as a matter of precaution we do not want to modify ArcGIS API for Python.
# To prevent this we use conda to install pyogrio with no dependencies.
# Because the geopandas version we installed comes from the esri channel and
# does not actually require pyogrio, this should be fine.
# If there are any issues related to this, they will most likely be expressed as
# import errors when attempting to use certain geopandas modules.
& conda install pyogrio>=0.7.2 --no-deps

& pip install -e (Join-Path $Env:AKDOF_ROOT "library/akdof_shared")

Write-Host "Conda environment '$($env:CONDA_DEFAULT_ENV)' setup complete. Exiting..."
& conda deactivate
exit