↩️ [Back to repository overview](../../README.md)

↩️ [Back to projects](../README.md)

# About

This project provides users of [Alaska Statewide Maps](https://alaska-division-of-forestry-and-fire-protection-nifc.hub.arcgis.com/pages/statewide-maps) with up-to-date KMZ layers for Avenza basemap customization. Layers are generated on a nightly or annual basis, depending on the potential change frequency of the input data source. All input data sources are ArcGIS Online hosted feature layers.

# Requirements

### Software
* Miniconda
* ArcGIS Pro
### Permissions
* MFA-exempt credentials for uploading Alaska Known Sites Database KMZ files to the [NIFC ArcGIS Online organization](https://nifc.maps.arcgis.com/home/index.html).
* Credentials for uploading the remaining KMZ files to the [NIFC FTP Server](https://ftp.wildfire.gov/).

# Adding New Input Data Sources

Extending this project to include a new ArcGIS Online input feature layer data source involves two steps:

1. Modify the [`INPUT_FEATURE_LAYERS_CONFIG`](./config/inputs_config.py#L88) global constant, following the established `input_kmz_layer_factory()` pattern to define a new input. 
2. Add a layer file with the desired output symbology to the [layer files](./data/layer_files) directory.
	* It is critical that the `alias` of your new input feature layer and the name of the associated layer file are an exact match.
	* You should verify that the symbology of the layer file transfers well to the KMZ file format.

