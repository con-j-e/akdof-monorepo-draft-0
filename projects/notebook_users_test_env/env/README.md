# Note to Self
incompatabilities between arcgis api for python and pyogrio (gpd dep) make this env tricky.
consider the following approaches to the build:

* maybe getting geopandas from the esri channel could circumvent the pyogrio issue?

1. get the team to switch to using the REST API (would need to validate if this is even feasible by looking at current notebooks).
2. do a --no-deps arcgis python api install, and resolve import errors one at a time (would need to begin experimenting with their projects to make them the envs)

**either approach begins with getting all notebooks into a folder structure and searching import pattern and arcgis usage. should request people send all these my way.**