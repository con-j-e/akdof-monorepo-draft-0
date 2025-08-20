from pathlib import Path
from datetime import timedelta
from typing import Literal

from akdof_shared.io.file_cache_manager import FileCacheManager, PurgeMethod
from akdof_shared.utils.create_file_diff import create_file_diff
from akdof_shared.gis.input_feature_layer import InputFeatureLayerCache, InputFeatureLayer, InputFeatureLayersConfig

from config.logging_config import FLM
from config.process_config import PROJ_DIR
from config.secrets_config import NIFC_TOKEN

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

def kmz_feature_layer_cache_factory(cache_path: Path) -> InputFeatureLayerCache:
    resource_info_fcm = FileCacheManager(
        path=cache_path / "resource_info",
        max_age=timedelta(days=1),
        max_count=3,
        purge_method=PurgeMethod.OLDEST_WHILE_MAX_COUNT_EXCEEDED,
        cache_compare_func=create_file_diff
    )
    features_fcm = FileCacheManager(
        path=cache_path / "features",
        max_age=timedelta(days=30),
        max_count=3,
    )
    input_feature_layer_cache = InputFeatureLayerCache(
        resource_info=resource_info_fcm,
        features=features_fcm,
    )
    return input_feature_layer_cache

def input_kmz_layer_factory(url: str, alias: str, token: str | None = None, sql_where_clause: str | None = None, processing_frequency: Literal["always", "annual"] = "always"):
    ifl = InputFeatureLayer(
        url=url,
        alias=alias,
        token=token,
        sql_where_clause=sql_where_clause,
        cache=kmz_feature_layer_cache_factory(cache_path=PROJ_DIR / "data" / "cache" / "input_feature_layers" / alias.lower().strip().replace(" ", "_")),
        processing_frequency=processing_frequency,
        logger=_LOGGER
    )
    return ifl

INPUT_FEATURE_LAYERS_CONFIG = InputFeatureLayersConfig((
    input_kmz_layer_factory(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Alaska_Known_Sites_Database_U5/FeatureServer/0",
        alias="AKSD",
        token=NIFC_TOKEN
    ),
    input_kmz_layer_factory(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/InternalView_NIFS_2025/FeatureServer/6",
        alias="EventPolygon",
        token=NIFC_TOKEN
    ),
    input_kmz_layer_factory(
        url="https://services1.arcgis.com/KbxwQRRfWyEYLgp4/ArcGIS/rest/services/AlaskaFireManagementOptions_Shaded/FeatureServer/0",
        alias="FireManagementOptions",
        sql_where_clause="FireManagementOption NOT IN ('Unplanned', 'Limited')",
        processing_frequency="annual",
    ),
    input_kmz_layer_factory(
        url="https://fire.ak.blm.gov/arcgis/rest/services/MapAndFeatureServices/FireHistory/FeatureServer/1",
        alias="FireHistory",
        sql_where_clause="FIREYEAR > '2014'",
        processing_frequency="annual",
    ),
    input_kmz_layer_factory(
        url="https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Forestry_Roads_Public_View/FeatureServer/0",
        alias="ForestRoads",
        sql_where_clause="Vehicle_Access_Type <> '3'",
        processing_frequency="annual",
    ),
    input_kmz_layer_factory(
        url="https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Forestry_Mile_Posts_Public_View/FeatureServer/0",
        alias="ForestMilePosts",
        processing_frequency="annual",
    ),
    input_kmz_layer_factory(
        url="https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/DOF_Bridges_Public_View/FeatureServer/0",
        alias="ForestBridges",
        processing_frequency="annual",
    ),
    input_kmz_layer_factory(
        url="https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Fuel_Treatments_Public_View/FeatureServer/0",
        alias="FuelTreatments",
        sql_where_clause="status NOT IN ('Planned', 'Recommended')",
    ),
    input_kmz_layer_factory(
        url="https://fire.ak.blm.gov/arcgis/rest/services/MapAndFeatureServices/Lightning/FeatureServer/1",
        alias="LightningYesterday",
    ),
    input_kmz_layer_factory(
        url="https://fire.ak.blm.gov/arcgis/rest/services/MapAndFeatureServices/Lightning/FeatureServer/0",
        alias="LightningToday",
    ),
    input_kmz_layer_factory(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/AK_Native_Allotments_OFFLINE/FeatureServer/0",
        alias="NativeAllotments",
        token=NIFC_TOKEN,
        processing_frequency="annual",
    ),
    input_kmz_layer_factory(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/InternalView_NIFS_2025/FeatureServer/5",
        alias="PerimeterLine",
        token=NIFC_TOKEN
    ),
    input_kmz_layer_factory(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Temporary_Flight_Restrictions_(Internal_View)/FeatureServer/0",
        alias="TFR",
        token=NIFC_TOKEN
    ),
    input_kmz_layer_factory(
        url="https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/Satellite_VIIRS_Thermal_Hotspots_and_Fire_Activity/FeatureServer/0",
        alias="VIIRS",
    ),
    input_kmz_layer_factory(
        url="https://fire.ak.blm.gov/arcgis/rest/services/MapAndFeatureServices/WaterSources/FeatureServer/0",
        alias="WaterSources",
        processing_frequency="annual",
    ),
))
INPUT_FEATURE_LAYERS_CONFIG.update_resource_info()