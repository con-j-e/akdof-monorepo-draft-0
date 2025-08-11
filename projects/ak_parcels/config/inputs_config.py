import asyncio
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from akdof_shared.io.file_cache_manager import FileCacheManager, PurgeMethod
from akdof_shared.io.async_requester import AsyncArcGisRequester
from akdof_shared.utils.create_file_diff import create_file_diff
from akdof_shared.gis.input_feature_layer import InputFeatureLayerCache, InputFeatureLayer, InputFeatureLayersConfig

from config.logging_config import FLM
from config.process_config import PROJ_DIR, TARGET_EPSG

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

_SHARED_SEMAPHORE = asyncio.Semaphore(15)
_SHARED_REQUESTER = AsyncArcGisRequester(logger=_LOGGER)
_SHARED_THREAD_EXECUTOR = ThreadPoolExecutor(thread_name_prefix="inputs_config")

def parcel_feature_layer_cache_factory(cache_path: Path) -> InputFeatureLayerCache:
    resource_info_fcm = FileCacheManager(
        path=cache_path / "resource_info",

        # a small max_age value is being used temporarily to help determine if resource info reliably changes whenever feature data changes
        max_age=timedelta(hours=1),
        
        max_count=3,
        purge_method=PurgeMethod.OLDEST_WHILE_MAX_COUNT_EXCEEDED,
        cache_compare_func=create_file_diff
    )
    features_fcm = FileCacheManager(
        path=cache_path / "features",
        max_age=timedelta(days=30),
        max_count=3,
        purge_method=PurgeMethod.OLDEST_WHILE_MAX_COUNT_EXCEEDED,
    )
    input_feature_layer_cache = InputFeatureLayerCache(
        resource_info=resource_info_fcm,
        features=features_fcm,
    )
    return input_feature_layer_cache

def input_parcel_factory(url: str, alias: str | None, field_map: dict[str, str], certificate_chain: Path | None = None) -> InputFeatureLayer:
    ifl = InputFeatureLayer(
        url=url,
        alias=alias,
        cache=parcel_feature_layer_cache_factory(cache_path=PROJ_DIR / "parcel_inputs_cache" / alias.lower().strip().replace(" ", "_")),
        certificate_chain=certificate_chain,
        output_epsg=TARGET_EPSG,
        outfields=[source_field for source_field in field_map.values() if source_field is not None],
        field_map={source_field: target_field for target_field, source_field in field_map.items() if source_field is not None},
        logger=_LOGGER,
        semaphore=_SHARED_SEMAPHORE,
        requester=_SHARED_REQUESTER,
        thread_executor=_SHARED_THREAD_EXECUTOR,
    )
    return ifl

INPUT_FEATURE_LAYERS_CONFIG = InputFeatureLayersConfig((
    input_parcel_factory(
        url="https://services2.arcgis.com/Ce3DhLRthdwbHlfF/ArcGIS/rest/services/PropertyInformation_Hosted/FeatureServer/0",
        alias="Anchorage Municipality",
        field_map = {
            "parcel_id": "Parcel_ID",
            "owner": "Owner_Name", 
            "alt_owner": None,
            "property_type": "Property_Type",
            "property_use": "Land_Use",
            "land_value": "Appraised_Land_Value",
            "building_value": "Appraised_Building_Value",
            "total_value": "Appraised_Total_Value",
        }
    ),
    input_parcel_factory(
        url="https://services8.arcgis.com/MqzStQjDmKoNl0E6/ArcGIS/rest/services/TaxParcels_Related/FeatureServer/0",
        alias="Bristol Bay Borough",
        field_map = {
            "parcel_id": "GlobalID",
            "owner": "First_Owner_Name", 
            "alt_owner": "Company_Owner_Name",
            "property_type": None,
            "property_use": None,
            "land_value": None,
            "building_value": None,
            "total_value": None,
        }
    ),
    input_parcel_factory(
        url="https://arcgis.dnr.alaska.gov/arcgis/rest/services/OpenData/Administrative_BoroughParcels/FeatureServer/1",
        alias="Denali Borough",
        field_map={
            "parcel_id": "GlobalID",
            "owner": "GRANTEE", 
            "alt_owner": None,
            "property_type": None,
            "property_use": None,
            "land_value": None,
            "building_value": None,
            "total_value": None,
        },
    ),
    input_parcel_factory(
        url="https://services3.arcgis.com/gdLTz4xpy5IxwbSz/arcgis/rest/services/ParcelsOnline/FeatureServer/0",
        alias="Dillingham Census Area",
        field_map={
            "parcel_id": "ParcelID",
            "owner": None,
            "alt_owner": None,
            "first_name": "FirstName", 
            "last_name": "LastName",
            "property_type": "OwnType",
            "property_use": "LandUse",
            "land_value": "LandValue",
            "building_value": "ImprovedValue",
            "total_value": "TotalValue",
        },
    ),
    input_parcel_factory(
        url="https://services.arcgis.com/f4rR7WnIfGBdVYFd/ArcGIS/rest/services/Tax_Parcels/FeatureServer/0",
        alias="Fairbanks North Star Borough",
        field_map={
            "parcel_id": "PAN",
            "owner": "Owner1", 
            "alt_owner": "Owner2",
            "property_type": "PARCEL_TYPE",
            "property_use": "Assessing_Primary_Use",
            "land_value": "Land_Value",
            "building_value": "Improvements",
            "total_value": "Total_Value",
        },
    ),
    input_parcel_factory(
        url="https://services3.arcgis.com/pMlUMMROURtJLUZt/ArcGIS/rest/services/ParcelsOnline/FeatureServer/0",
        alias="Haines Borough",
        field_map={
            "parcel_id": "PIN",
            "owner": "OWNER1", 
            "alt_owner": "Company",
            "property_type": "OWNTYPE",
            "property_use": "LandType",
            "land_value": "LAND",
            "building_value": "BLDG",
            "total_value": "TOTAL",
        },
    ),
    input_parcel_factory(
        url="https://services.arcgis.com/kpMKjjLr8H1rZ4XO/arcgis/rest/services/Juneau_Parcel_Viewer/FeatureServer/0",
        alias="Juneau City & Borough",
        field_map={
            "parcel_id": "tax_id",
            "owner": None,
            "alt_owner": None,
            "property_type": "feat_type",
            "property_use": None,
            "land_value": None,
            "building_value": None,
            "total_value": None,
        },
    ),
    input_parcel_factory(
        url="https://services.arcgis.com/ba4DH9pIcqkXJVfl/ArcGIS/rest/services/Redacted_Parcels_view/FeatureServer/0",
        alias="Kenai Peninsula Borough",
        field_map={
            "parcel_id": "PARCEL_ID",
            "owner": "OWNER",
            "alt_owner": "ATTENTION",
            "property_type": "OWN_TYPE_1",
            "property_use": "USE_TYPE_1",
            "land_value": "LAND_VALUE",
            "building_value": "IMPROVEMENT_VALUE",
            "total_value": "ASSESSED_VALUE",
        },
    ),
    input_parcel_factory(
        url="https://services2.arcgis.com/65jtiGuzdaRB5FxF/ArcGIS/rest/services/KetchikanAKFeatures/FeatureServer/0",
        alias="Ketchikan Borough",
        field_map={
            "parcel_id": "PARCELNO",
            "owner": "Owner_Name",
            "alt_owner": "Owner_2",
            "property_type": "Prop_Type",
            "property_use": "PropUse",
            "land_value": "Asd_Land_V",
            "building_value": "Asd_Imp_Va",
            "total_value": "Total_Asse",
        },
    ),
    input_parcel_factory(
        url="https://services1.arcgis.com/R5BNizttyFKxRSMm/arcgis/rest/services/KIB_Parcels/FeatureServer/0",
        alias="Kodiak Island Borough",
        field_map={
            "parcel_id": "Parcels_prop_id",
            "owner": "PACS_Data_file_as_name",
            "alt_owner": None,
            "property_type": "PACS_Data_Zone_Type",
            "property_use": "PACS_Data_Usage",
            "land_value": "CertifiedRoll2025_Land_Value",
            "building_value": "CertifiedRoll2025_Build_Value",
            "total_value": "CertifiedRoll2025_Total_Value",
        },
    ),
    input_parcel_factory(
        url="https://maps.matsugov.us/map/rest/services/OpenData/Cadastral_Parcels/FeatureServer/0",
        alias="Matanuska-Susitna Borough",
        field_map={
            "parcel_id": "P_ID",
            "owner": "OWNER_1",
            "alt_owner": "Buyer_Name",
            "property_type": "FTYPE",
            "property_use": "GENOWN",
            "land_value": "LANDVALUE",
            "building_value": "BLDGVALUE",
            "total_value": None,
        },
        certificate_chain=Path(r"C:\CERTS\maps.matsugov.us_chain.pem")
    ),
    input_parcel_factory(
        url="https://services9.arcgis.com/Oi9vFzXc8ZcONgM6/arcgis/rest/services/Parcels_Joined_with_Taxroll_Symbolized_by_Exempt/FeatureServer/0",
        alias="Nome Census Area",
        field_map={
            "parcel_id": "ACCTNUMBER",
            "owner": "Name",
            "alt_owner": None,
            "property_type": "Polygon_Type",
            "property_use": None,
            "land_value": "LandMarketValue",
            "building_value": "BuildingMarketValue",
            "total_value": "TotalMarketValue",
        },
    ),
    input_parcel_factory(
        url="https://gis-public.north-slope.org/server/rest/services/Lama/Parcels_sql/FeatureServer/9",
        alias="North Slope Borough",
        field_map={
            "parcel_id": "Parcel_ID",
            "owner": None,
            "alt_owner": None,
            "first_name": "First_Name",
            "last_name": "Last_Name",
            "property_type": "OwnerTypeDesc",
            "property_use": "LUCDesc",
            "land_value": None,
            "building_value": None,
            "total_value": None,
        },
    ),
    input_parcel_factory(
        url="https://services7.arcgis.com/RqATEQTpM1W1xU9c/ArcGIS/rest/services/Lots/FeatureServer/0",
        alias="Petersburg Borough",
        field_map={
            "parcel_id": "Parcel_ID",
            "owner": "OWNER",
            "alt_owner": None,
            "property_type": "ZONING",
            "property_use": "Parcel_Use",
            "land_value": "Gross_Land",
            "building_value": "Gross_Impr",
            "total_value": "Total_Gros",
        },
    ),
    input_parcel_factory(
        url="https://services7.arcgis.com/EozEvrS4g3SEhtG3/ArcGIS/rest/services/Sitka_Parcels_2022/FeatureServer/0",
        alias="Sitka City & Borough",
        field_map={
            "parcel_id": "MSPARCELID",
            "owner": "MSOWNERA",
            "alt_owner": "MSOWNERB",
            "property_type": "MSZONING",
            "property_use": "MSLANDUSED",
            "land_value": "MSTAXLND",
            "building_value": "MSVALBLD",
            "total_value": "MSVALTOT",
        },
    ),
    input_parcel_factory(
        url="https://services7.arcgis.com/7cBSaoaaRaH5ojZy/arcgis/rest/services/Parcels/FeatureServer/0",
        alias="Wrangell City & Borough",
        field_map={
            "parcel_id": "PARCELNUM",
            "owner": None,
            "alt_owner": None,
            "first_name": "FIRST_NAME",
            "last_name": "LAST_NAME",
            "property_type": "LEGAL_DESC1",
            "property_use": "USE_CODE",
            "land_value": "LAND_VALUE",
            "building_value": "IMPR_VALUE",
            "total_value": "TOTAL_VALUE",
        },
    ),
    input_parcel_factory(
        url="https://services2.arcgis.com/gRKiTtxkoTx0gERB/ArcGIS/rest/services/ParcelsOnline/FeatureServer/0",
        alias="Yakutat City & Borough",
        field_map={
            "parcel_id": "ParcelID",
            "owner": "FullName",
            "alt_owner": "Owner",
            "property_type": "OwnType",
            "property_use": "Landuse",
            "land_value": "LandValue",
            "building_value": "ImprovedValue",
            "total_value": "TotalValue",
        },
    ),
))