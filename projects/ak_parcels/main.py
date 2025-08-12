import asyncio
import sys

from akdof_shared.protocol.main_exit_manager import MainExitManager, ExitStatus, CleanupCallable, CleanExitFailure
from akdof_shared.protocol.datetime_info import now_utc_iso

from config.process_config import PROJ_DIR, TARGET_LAYER_CONFIG
from config.logging_config import FLM
from config.inputs_config import INPUT_FEATURE_LAYERS_CONFIG
from config.secrets_config import SOA_ARCGIS_AUTH, GMAIL_SENDER
from core.extract_parcel_inputs import load_parcel_feature_history, identify_parcel_features_to_update
from core.update_target_layer import update_target_layer, target_feature_count_validation

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
        features_to_update = identify_parcel_features_to_update(feature_history_results=feature_history_results)

        token = SOA_ARCGIS_AUTH.checkout_token(minutes_needed=45)
        await update_target_layer(target_layer_config=TARGET_LAYER_CONFIG, token=token, features_to_update=features_to_update)
        target_feature_count_validation()

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