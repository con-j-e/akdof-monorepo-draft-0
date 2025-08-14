from akdof_shared.gis.input_feature_layer import InputFeatureLayer, InputFeatureLayersConfig

INPUT_FEATURE_LAYERS_CONFIG = InputFeatureLayersConfig((
    InputFeatureLayer(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Alaska_Known_Sites_Database_U5/FeatureServer/0",
        alias="AKSD",
    ),
    InputFeatureLayer(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/InternalView_NIFS_2025/FeatureServer/6",
        alias="EventPolygon",
    ),
    InputFeatureLayer(
        url="https://services1.arcgis.com/KbxwQRRfWyEYLgp4/ArcGIS/rest/services/AlaskaFireManagementOptions_Shaded/FeatureServer/0",
        alias="FireManagementOptions",
        sql_where_clause="FireManagementOption NOT IN ('Unplanned', 'Limited')",
        processing_frequency="annual",
    ),
    InputFeatureLayer(
        url="https://fire.ak.blm.gov/arcgis/rest/services/MapAndFeatureServices/FireHistory/FeatureServer/1",
        alias="FireHistory",
        sql_where_clause="FIREYEAR > '2014'",
        processing_frequency="annual",
    ),
    InputFeatureLayer(
        url="https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Forestry_Roads_Public_View/FeatureServer/0",
        alias="ForestRoads",
        sql_where_clause="Vehicle_Access_Type <> '3'",
        processing_frequency="annual",
    ),
    InputFeatureLayer(
        url="https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Forestry_Mile_Posts_Public_View/FeatureServer/0",
        alias="ForestMilePosts",
        processing_frequency="annual",
    ),
    InputFeatureLayer(
        url="https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/DOF_Bridges_Public_View/FeatureServer/0",
        alias="ForestBridges",
        processing_frequency="annual",
    ),
    InputFeatureLayer(
        url="https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Fuel_Treatments_Public_View/FeatureServer/0",
        alias="FuelTreatments",
        sql_where_clause="status NOT IN ('Planned', 'Recommended')",
    ),
    InputFeatureLayer(
        url="https://fire.ak.blm.gov/arcgis/rest/services/MapAndFeatureServices/Lightning/FeatureServer/1",
        alias="LightningYesterday",
    ),
    InputFeatureLayer(
        url="https://fire.ak.blm.gov/arcgis/rest/services/MapAndFeatureServices/Lightning/FeatureServer/0",
        alias="LightningToday",
    ),
    InputFeatureLayer(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/AK_Native_Allotments_OFFLINE/FeatureServer/0",
        alias="NativeAllotments",
        processing_frequency="annual",
    ),
    InputFeatureLayer(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/InternalView_NIFS_2025/FeatureServer/5",
        alias="PerimeterLine",
    ),
    InputFeatureLayer(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Temporary_Flight_Restrictions_(Internal_View)/FeatureServer/0",
        alias="TFR",
    ),
    InputFeatureLayer(
        url="https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/Satellite_VIIRS_Thermal_Hotspots_and_Fire_Activity/FeatureServer/0",
        alias="VIIRS",
    ),
    InputFeatureLayer(
        url="https://fire.ak.blm.gov/arcgis/rest/services/MapAndFeatureServices/WaterSources/FeatureServer/0",
        alias="WaterSources",
        processing_frequency="annual",
    ),
))