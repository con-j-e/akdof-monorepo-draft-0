import arcpy

from akdof_shared.utils.with_retry import with_retry
from akdof_shared.protocol.file_logging_manager import ExitStatus

from config.logging_config import FLM
from config.inputs_config import INPUT_FEATURE_LAYERS_CONFIG
from config.process_config import (
    AK_FIRE_REGIONS_GDB,
    AK_FIRE_REGIONS_LAYER_NAME,
    LYRX_DIRECTORY,
    OUTPUT_KMZ_DIRECTORY,
    PROCESSING_CYCLE,
    PROCESSING_REGIONS,
)
from config.secrets_config import NIFC_AGOL_CREDENTIALS

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

def arcpy_create_kmzs() -> ExitStatus:
    try:
        exit_status = ExitStatus.OK

        with_retry(arcpy.SignInToPortal, *NIFC_AGOL_CREDENTIALS)
        arcpy.env.workspace = str(AK_FIRE_REGIONS_GDB)
        arcpy.env.overwriteOutput = True
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)
        arcpy.env.parallelProcessingFactor = 100

        if PROCESSING_CYCLE == "annual":
            input_feature_layers_config = [input for input in INPUT_FEATURE_LAYERS_CONFIG if input.processing_frequency == "annual"]
        else:
            input_feature_layers_config = [input for input in INPUT_FEATURE_LAYERS_CONFIG]

        arcpy_processing_exceptions = dict()
        for region in PROCESSING_REGIONS:
            selected_region = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=AK_FIRE_REGIONS_LAYER_NAME,
                selection_type="NEW_SELECTION",
                where_clause=rf"REGION = '{region}'",
            )
            for input in input_feature_layers_config:
                try:
                    with_retry(
                        _clip_layer_to_kmz,
                        clip_layer=selected_region,
                        layer_to_clip=str(input.url),
                        layer_file=str(LYRX_DIRECTORY / f"{input.alias}.lyrx"),
                        output_path=str(OUTPUT_KMZ_DIRECTORY / f"{region}_{input.alias}.kmz"),
                        query=input.sql_where_clause,
                        retry_logger=_LOGGER,
                    )
                    _LOGGER.info(f"_clip_layer_to_kmz() --> {region}_{input.alias}.kmz")
                except Exception as e:
                    if input.alias not in arcpy_processing_exceptions:
                        arcpy_processing_exceptions[input.alias] = FLM.format_exception(exc_val=e, full_traceback=True)

        if arcpy_processing_exceptions:
            _LOGGER.error("Errors occurred during ArcPy processing and persisted across all retry attempts!")
            for feature_layer_alias, logged_exc in arcpy_processing_exceptions.items():
                _LOGGER.error(f"{feature_layer_alias}: {logged_exc}")

    except Exception as e:
        exit_status = ExitStatus.CRITICAL
        _LOGGER.critical(FLM.format_exception(exc_val=e, full_traceback=True))

    finally:
        return exit_status
    
def _clip_layer_to_kmz(
    clip_layer: str, layer_to_clip: str, layer_file: str, output_path: str, query: str | None = None
) -> None:
    """
    ArcPy dependent function that clips a layer, optionally applies a SQL where-clause, and applies symbology from a layer file prior to saving a .kmz output.

    Parameters
    ----------
    clip_layer : str
        Passed to arcpy.analysis.Clip() as the clip_features argument.
    layer_to_clip : str
        Passed to arcpy.analysis.Clip() as the in_features argument.
    layer_file : str
        File path to .lyrx that will be used to apply symbology prior to converting clipped layer to KMZ.
    output_path : str
        File path to desired output location.
    query : str | None, optional
        Standard SQL query passed to arcpy.Management.MakeFeatureLayer() as the where_clause argument, applies filter prior to KMZ conversion. By default None.
    """
    memory_clip = r"memory\service_clip"
    memory_layer = r"memory\clip_feature_layer"

    arcpy.analysis.Clip(in_features=layer_to_clip, clip_features=clip_layer, out_feature_class=memory_clip)
    arcpy.management.MakeFeatureLayer(in_features=memory_clip, out_layer=memory_layer, where_clause=query)

    symbolized_layer = arcpy.management.ApplySymbologyFromLayer(in_layer=memory_layer, in_symbology_layer=layer_file)
    symbolized_layer_path = symbolized_layer[0]

    arcpy.conversion.LayerToKML(
        layer=symbolized_layer_path,
        out_kmz_file=output_path,
        is_composite="NO_COMPOSITE",
        ignore_zvalue="CLAMPED_TO_GROUND",
    )
