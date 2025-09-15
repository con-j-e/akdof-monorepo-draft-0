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

# When building an environment that includes core ESRI packages (ArcGIS API for Python, ArcPy),
# we override our .condarc channel preferences:
# Check the ESRI channel for packages before checking conda-forge,
# and use a 'flexible' channel priority instead of 'strict'.
$env:CONDA_CHANNELS = "esri,conda-forge"
$env:CONDA_CHANNEL_PRIORITY = "flexible"

# We explicitly get the following packages from the ESRI channel:
# arcgis (for a complete install of the ArcGIS API for Python; this package is only available on the ESRI channel).
# geopandas (required by the akdof_shared package; it is essential that we use ESRI's version, due to conflicts between pyogrio and core ESRI packages).
& conda create --prefix ./conda_env --channel esri arcgis geopandas

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

# People on our team like to use notebooks during development,
# and ipykernel is a minimum requirement for .ipynb functionality in VS Code.
& conda install ipykernel

# The following packages are required by the akdof_shared package.
# We install them from ESRI (or conda-forge if not available from ESRI),
# without updating or changing any of the already installed dependencies.
# This is done defensively to ensure we don't modify core ESRI package dependencies.
& conda install --freeze-installed `
    aiodns `
    aiohttp `
    argon2-cffi `
    jaraco.classes `
    more-itertools `
    pycryptodome

# Although we have ESRI's geopandas version installed (which does not use pyogrio),
# if we don't have pyogrio installed pip will attempt to install pyogrio with all of its dependencies while installing akdof_shared.
# So we pre-emptively install pyogrio with no dependencies using conda. 
& conda install pyogrio --no-deps

& pip install -e (Join-Path $Env:AKDOF_ROOT "library/akdof_shared")

Write-Host "Conda environment '$($env:CONDA_DEFAULT_ENV)' setup complete. Exiting..."
& conda deactivate
exit