import subprocess
import sys

from akdof_shared.protocol.file_logging_manager import ExitStatus
from akdof_shared.protocol.main_exit_manager import MainExitManager

from config.logging_config import FLM
from config.process_config import AKSD_KMZ_ITEM_IDS, OUTPUT_KMZ_DIRECTORY, PROCESSING_REGIONS, PROJ_DIR
from config.secrets_config import (
    NIFC_FTP_CREDENTIALS,
    NIFC_ARCGIS_AUTH,
    GMAIL_SENDER
)
from core.agol_upload_aksd_kmzs import agol_upload_aksd_kmzs
from core.ftp_upload_kmzs import ftp_upload_kmzs

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

class ArcPySubprocessCriticalError(Exception): 
    """An error occurred in the ArcPy subprocess that warrants premature termination of the main program"""
    pass

def main() -> ExitStatus:
    with MainExitManager(
        project_directory=PROJ_DIR,
        file_logging_manager=FLM,
        main_logger=_LOGGER,
        gmail_sender=GMAIL_SENDER,
    ) as exit_manager:
        
        # kmz outputs are created using arcpy
        # arcpy is contained in a subprocess to prevent its imports from modifying the main runtime environment
        # _subprocess.py exits using the ExitStatus enum (1 indicates an "operations normal" status)
        result = subprocess.run([sys.executable, str(PROJ_DIR / "_subprocess.py")], timeout=3600)
        if result.returncode != 1:
            raise ArcPySubprocessCriticalError(f"Exit Status: {result.returncode}. Check logs for details.")

        # alaska known sites database kmzs will be uploaded to nifc arcgis online
        try:
            nifc_token = NIFC_ARCGIS_AUTH.checkout_token(minutes_needed=5)
            agol_upload_aksd_kmzs(output_kmz_directory=OUTPUT_KMZ_DIRECTORY, aksd_kmz_item_ids=AKSD_KMZ_ITEM_IDS, token=nifc_token)
        except Exception as e:
            _LOGGER.critical(FLM.format_exception(exc_val=e, full_traceback=True))

        # remaining kmzs will be uploaded to ftp.wildfire.gov
        ftp_upload_kmzs(
            processing_regions=PROCESSING_REGIONS,
            output_kmz_directory=OUTPUT_KMZ_DIRECTORY,
            ftp_username=NIFC_FTP_CREDENTIALS.username,
            ftp_password=NIFC_FTP_CREDENTIALS.password,
        )

    return exit_manager.exit_status or ExitStatus.CRITICAL

if __name__ == "__main__":
    sys.exit(main())
