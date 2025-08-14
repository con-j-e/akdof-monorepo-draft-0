from datetime import datetime as dt
from datetime import timezone as tz
import os
from pathlib import Path
import subprocess
import sys

from arcgis.gis import GIS

from akdof_shared.protocol.file_logging_manager import ExitStatus
from akdof_shared.protocol.datetime_info import now_utc_iso
from akdof_shared.utils.with_retry import with_retry

from akwf_utils.exit_protocol import ExitStatus
from akwf_utils.logging_utils import FileLoggingManager as LogManager
from akwf_utils.logging_utils import format_logged_exception
from akwf_utils.retry_utils import with_retry
from akwf_utils.time_utils import now_utc_iso

from config.logging_config import FLM
from config.process_config import AKSD_KMZ_ITEM_IDS, OUTPUT_KMZ_DIRECTORY, PROCESSING_REGIONS, PROJ_DIR
from config.secrets_config import (
    NIFC_AGOL_CREDENTIALS,
    NIFC_FTP_CREDENTIALS,
)
from core.arcgis_api_upload_aksd_kmzs import upload_aksd_kmzs
from core.ftp_upload_kmzs import upload_kmzs

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

def main() -> ExitStatus:
    """
    Entry point for converting hosted feature layers to KMZ files and uploading KMZ files to ftp.wildfire.gov or ArcGIS Online.

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
        logger = LogManager.get_file_logger(name=__name__, log_file=PROJ_DIR / "logs" / f"{Path(__file__).stem}.log")
        _LOGGER.info("PROCESS START")

        # kmz outputs are created using arcpy
        # arcpy is contained in a subprocess to prevent it from modifying the main runtime environment
        env = dict(**os.environ)
        existing_path = os.environ.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent) + os.pathsep + existing_path
        subprocess.run(
            [sys.executable, str(PROJ_DIR / "core" / "arcpy_create_kmzs.py")], env=env, check=True, timeout=3600
        )

        # alaska known sites database kmzs will be uploaded to nifc arcgis online
        try:
            gis = with_retry(GIS, *NIFC_AGOL_CREDENTIALS)
            upload_aksd_kmzs(output_kmz_directory=OUTPUT_KMZ_DIRECTORY, aksd_kmz_item_ids=AKSD_KMZ_ITEM_IDS, gis=gis)
        except Exception as e:
            _LOGGER.critical(format_logged_exception(type(e), e, e.__traceback__))

        # remaining kmzs will be uploaded to ftp.wildfire.gov
        upload_kmzs(
            processing_regions=PROCESSING_REGIONS,
            output_kmz_directory=OUTPUT_KMZ_DIRECTORY,
            ftp_username=NIFC_FTP_CREDENTIALS.username,
            ftp_password=NIFC_FTP_CREDENTIALS.password,
        )

        _LOGGER.info("PROCESS FINISHED")

    except Exception as e:
        _LOGGER.critical(format_logged_exception(type(e), e, e.__traceback__))

    finally:
        try:
            # because arcpy is called with a subprocess, main.py LogManager is not aware of the file the subprocess logs to
            # so log files need to be passed explicitly to LogManager
            python_logging_files = [file for file in (PROJ_DIR / "logs").glob("*.log")]

            LogManager.flush_all_handlers()
            exit_status = LogManager.check_log_files_for_status(start_datetime, log_files_to_check=python_logging_files)
            log_check_emails = LogManager.write_log_check_emails(
                log_files_to_check=python_logging_files, previous_hours=2
            )
            for file_name, log_messages in log_check_emails.items():
                send_gmail(
                    f"LOGGING NOTIFICATION: {PROJ_DIR.stem}, {file_name}", "\n\n".join(log_messages), *SEND_GMAIL_PARAMS
                )
            LogManager.close_all_handlers()
            LogManager.check_log_files_to_archive(
                PROJ_DIR / "logs" / "archive", log_files_to_check=python_logging_files
            )
        except Exception as e:
            exit_status = ExitStatus.CRITICAL
            shutdown_error = format_logged_exception(type(e), e, e.__traceback__)
            print(f"{now_utc_iso()} | {shutdown_error}", file=sys.stderr)
        finally:
            exit_status = ExitStatus.CRITICAL if exit_status is None else exit_status
            return exit_status


if __name__ == "__main__":
    sys.exit(main())
