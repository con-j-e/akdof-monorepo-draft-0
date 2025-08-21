import asyncio
import sys

from akdof_shared.protocol.main_exit_manager import AsyncMainExitManager, CleanupCallable, EarlyExitSignal
from akdof_shared.protocol.file_logging_manager import ExitStatus

from config.process_config import PROJ_DIR, TARGET_LAYER_CONFIG
from config.logging_config import FLM
from config.inputs_config import INPUT_FEATURE_LAYERS_CONFIG
from config.secrets_config import SOA_ARCGIS_AUTH, GMAIL_SENDER
from core.extract_parcel_inputs import load_parcel_feature_history, identify_parcel_features_to_update
from core.update_target_layer import update_target_layer, target_feature_count_validation

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)
    
async def main() -> ExitStatus:
    async with AsyncMainExitManager(
        project_directory=PROJ_DIR,
        file_logging_manager=FLM,
        main_logger=_LOGGER,
        gmail_sender=GMAIL_SENDER,
        cleanup_callables=(
            CleanupCallable(INPUT_FEATURE_LAYERS_CONFIG.shutdown_thread_executors),
            CleanupCallable(INPUT_FEATURE_LAYERS_CONFIG.close_requesters)
        )
    ) as exit_manager:

        feature_history_results = await load_parcel_feature_history()
        features_to_update = identify_parcel_features_to_update(feature_history_results=feature_history_results)
        if not features_to_update:
            raise EarlyExitSignal

        token = SOA_ARCGIS_AUTH.checkout_token(minutes_needed=45)
        await update_target_layer(target_layer_config=TARGET_LAYER_CONFIG, token=token, features_to_update=features_to_update)
        target_feature_count_validation()

    return exit_manager.exit_status or ExitStatus.CRITICAL

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))