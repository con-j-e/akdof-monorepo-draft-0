import asyncio
import sys

from datetime import datetime as dt, timezone as tz
import pandas as pd
from pathlib import Path

from config.py.process_config import PROJ_DIR, LOG_LEVEL
from config.py.inputs_config import INPUT_FEATURE_LAYERS_CONFIG
from config.py.secrets_config import PKM
from core.extract_parcel_inputs import load_parcel_feature_history, identify_parcel_features_to_update
from core.update_target_layer import update_target_layer

from akwf_utils.logging_utils import FileLoggingManager as LogManager, format_logged_exception
from akwf_utils.exit_protocol import ExitStatus
from akwf_gis.arcgis_helpers import get_feature_count_and_extent
from akwf_gis.arcgis_gdf_conversion_prep import ArcGisTargetLayerConfig
from akwf_security.api_auth_manager import ArcGisApiAuthManager

pd.set_option("mode.chained_assignment", "raise")

_LOGGER = LogManager.get_file_logger(name=__name__, log_file=PROJ_DIR / "logs" / f"{Path(__file__).stem}.log", log_level=LOG_LEVEL)
    
async def main() -> ExitStatus:
    """
    

    Returns
    -------
    ExitStatus
        Status codes that all Python programs run as __main__ are expected to exit with.
        These codes represent the highest severity level of one or more events that occurred.
    """
    try:
        exit_status = None
        start_datetime = dt.now(tz.utc)
        LogManager.get_file_logger(name=None, log_file=PROJ_DIR / "logs" / f"root.log", log_level="DEBUG")
        _LOGGER.info("PROCESS START")

        feature_history_results = await load_parcel_feature_history()
        features_to_update = identify_parcel_features_to_update(feature_history_results=feature_history_results)

        PKM.setup_cryptfile_keyring()
        token = ArcGisApiAuthManager.checkout_token(service_name=r"https://soa-dnr.maps.arcgis.com/", username="for_admin", minutes_needed=30)
        
        target_layer_config = ArcGisTargetLayerConfig.load(
            json_path=PROJ_DIR / "config" / "json" / "target_layer_config" / "ak_parcels.json"
        )

        await update_target_layer(target_layer_config=target_layer_config, token=token, features_to_update=features_to_update)

        # try except inside loop. one of these queries could blow up. must attempt all validations
        for input_feature_layer in INPUT_FEATURE_LAYERS_CONFIG:
            source_count, _ = input_feature_layer._get_feature_count_and_extent()
            target_count, _ = get_feature_count_and_extent(base_url=target_layer_config["url"], where=f"local_gov = '{input_feature_layer.alias}'")
            if source_count != target_count:
                _LOGGER.error(f"{input_feature_layer.alias} has a feature count discrepency of {source_count - target_count} between source layer ({source_count}) and target layer ({target_count}).")
            else:
                _LOGGER.info(f"{input_feature_layer.alias} source and target feature counts are an exact match: {target_count}")

    except Exception as e:
        _LOGGER.critical(format_logged_exception(exc_val=e, full_traceback=True))

    finally:
        INPUT_FEATURE_LAYERS_CONFIG.shutdown_thread_executors()
        await INPUT_FEATURE_LAYERS_CONFIG.close_requesters()
        return exit_status or 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))