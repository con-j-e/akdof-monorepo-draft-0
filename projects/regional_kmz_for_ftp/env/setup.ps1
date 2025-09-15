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
# arcpy-base version 3.5 (for programmatic use of ArcGIS Pro geoprocessing tools; this package is only available on the ESRI channel).
# geomet (required by the akdof_shared package; we prefer ESRI's version because we trust them to maintain the package they use internally for conversions between ArcGIS JSON and GeoJSON data formats).
# geopandas (required by the akdof_shared package; it is essential that we use ESRI's version, due to conflicts between pyogrio and core ESRI packages).
& conda create --prefix ./conda_env --channel esri arcpy-base=3.5 geomet geopandas

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

# The following packages are required by the akdof_shared package.
# We install them from ESRI (or conda-forge if not available from ESRI),
# without updating or changing any of the already installed dependencies.
# This is done defensively to ensure we don't modify core ESRI package dependencies.
& conda install --freeze-installed `
    aiodns `
    aiohttp `
    argon2-cffi `
    jaraco.classes `
    keyring `
    more-itertools `
    pycryptodome `
    pydantic

# Although we have ESRI's geopandas version installed (which does not use pyogrio),
# if we don't have pyogrio installed pip will attempt to install pyogrio with all of its dependencies while installing akdof_shared.
# So we pre-emptively install pyogrio with no dependencies using conda. 
& conda install pyogrio --no-deps

& pip install -e (Join-Path $Env:AKDOF_ROOT "library/akdof_shared")

Write-Host "Conda environment '$($env:CONDA_DEFAULT_ENV)' setup complete. Exiting..."
& conda deactivate
exit