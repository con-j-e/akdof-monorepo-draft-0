# About

This project updates the [Alaska Statewide Parcels](https://soa-dnr.maps.arcgis.com/home/item.html?id=458be3d8aafa47cd882af05cee983f6b) ArcGIS Online hosted feature layer. Updates are triggered when changes are detected in an input parcel data source. All input data sources are ArcGIS Online hosted feature layers.

---
# Requirements

## Software
* Miniconda
## Permissions
* Credentials for updating an ArcGIS Online hosted feature layer that is owned by the [Alaska Department of Natural Resources](https://soa-dnr.maps.arcgis.com/home/index.html)

---
# Adding New Input Data Sources

Extending this project to include a new ArcGIS Online input feature layer data source involves one step. The same approach can be used to edit how input fields are mapped to the target layer schema (this can be necessary if an existing input data source has a schema change).

1. Modify the [`INPUT_FEATURE_LAYERS_CONFIG`](./config/inputs_config.py#L60) global constant, following the established `input_parcel_factory()` pattern to define a new input or edit the configuration of an existing input.

