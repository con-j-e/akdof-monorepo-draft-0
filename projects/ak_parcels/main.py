import asyncio
import sys

from akdof_shared.protocol.main_exit_manager import MainExitManager, ExitStatus, CleanupCallable, CleanExitFailure
from akdof_shared.protocol.datetime_info import now_utc_iso
from akdof_shared.gis.arcgis_helpers import get_feature_count_and_extent

from config.process_config import PROJ_DIR, TARGET_LAYER_CONFIG
from config.logging_config import FLM
from config.inputs_config import INPUT_FEATURE_LAYERS_CONFIG
from config.secrets_config import SOA_ARCGIS_AUTH, GMAIL_SENDER
from core.extract_parcel_inputs import load_parcel_feature_history, identify_parcel_features_to_update
from core.update_target_layer import update_target_layer

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)
    
async def main() -> ExitStatus:

    try:

        exit_manager = MainExitManager(
            project_directory=PROJ_DIR,
            file_logging_manager=FLM,
            main_logger=_LOGGER,
            gmail_sender=GMAIL_SENDER,
            cleanup_callables=(
                CleanupCallable(INPUT_FEATURE_LAYERS_CONFIG.shutdown_thread_executors),
                CleanupCallable(INPUT_FEATURE_LAYERS_CONFIG.close_requesters)
            )
        )

        feature_history_results = await load_parcel_feature_history()
        #features_to_update = identify_parcel_features_to_update(feature_history_results=feature_history_results)

        #token = SOA_ARCGIS_AUTH.checkout_token(minutes_needed=45)
        #await update_target_layer(target_layer_config=TARGET_LAYER_CONFIG, token=token, features_to_update=features_to_update)

        for input_feature_layer in INPUT_FEATURE_LAYERS_CONFIG:
            try:
                source_count, _ = input_feature_layer._get_feature_count_and_extent()
                target_count, _ = get_feature_count_and_extent(base_url=TARGET_LAYER_CONFIG.url, where=f"local_gov = '{input_feature_layer.alias}'")
                if source_count != target_count:
                    _LOGGER.error(f"{input_feature_layer.alias} has a feature count discrepency of {source_count - target_count} between source layer ({source_count}) and target layer ({target_count}).")
                else:
                    _LOGGER.info(f"{input_feature_layer.alias} source and target feature counts are an exact match: {target_count}")
            except Exception as e:
                _LOGGER.error(f"Resulting feature count validation failed with Exception: {FLM.format_exception(e)}")

    except Exception as e:
        _LOGGER.critical(FLM.format_exception(exc_val=e, full_traceback=True))

    finally:
        try:
            return await exit_manager.clean_exit_async()
        except CleanExitFailure as e:
            print(f"{now_utc_iso()} | {FLM.format_exception(exc_val=e, full_traceback=True)}", file=sys.stderr)
            return ExitStatus.CRITICAL

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))