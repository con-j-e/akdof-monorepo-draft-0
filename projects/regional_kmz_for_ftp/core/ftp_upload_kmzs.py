import ftplib
from pathlib import Path
from typing import Iterable

from akdof_shared.utils.with_retry import with_retry

from config.logging_config import FLM

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

def ftp_upload_kmzs(processing_regions: Iterable[str], output_kmz_directory: Path, ftp_username: str, ftp_password: str) -> None:
    """
    Connects to the wildfire.gov FTP server and uploads KMZ files to region-specific directories.
    Alaska Known Sites Database KMZ files, if present, will be skipped.
    Successfully uploaded files are moved to an 'ftp_complete' subdirectory.
    Upload failures are logged but do not interrupt processing of remaining files.

    Parameters
    ----------
    processing_regions : Iterable[str]
        Region names used for directory navigation and file filtering.
    output_kmz_directory : Path
        Directory containing the KMZ files to upload.
    ftp_username : str
        FTP server username.
    ftp_password : str
        FTP server password.
    """
    with Explicit_FTP_TLS(timeout=30) as ftps:
        ftps.connect(host="ftp.wildfire.gov", port=1021)
        ftps.login(user=ftp_username, passwd=ftp_password)
        ftps.prot_p()
        for region in processing_regions:
            ftps.cwd(f"/incident_specific_data/alaska/Statewide_Maps/{region}/Map_Layers")
            _LOGGER.info(f"Beginning uploads for {ftps.pwd()}")
            for kmz_file in output_kmz_directory.glob(f"{region}*.kmz"):
                if "AKSD" in kmz_file.name:
                    continue
                try:
                    with open(kmz_file, "rb") as file:
                        response_code = with_retry(
                            ftps.storbinary, cmd=f"STOR {kmz_file.name}", fp=file, retry_logger=_LOGGER
                        )
                    if response_code.startswith("226"):
                        _LOGGER.info(f"{kmz_file.name}: {response_code}")
                        kmz_file.replace(output_kmz_directory / "ftp_complete" / kmz_file.name)
                    else:
                        raise ftplib.error_reply(f"{kmz_file.name}: {response_code}")
                except ftplib.all_errors as e:
                    _LOGGER.error(FLM.format_exception(exc_val=e, full_traceback=True))

class Explicit_FTP_TLS(ftplib.FTP_TLS):
    """
    Explicit FTPS connection with shared TLS session.
    
    Extends FTP_TLS to properly handle data connections by reusing the 
    control connection's TLS session for data transfers.
    """

    def ntransfercmd(self, cmd, rest=None) -> tuple:
        """Create data connection with shared TLS session."""
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(conn, server_hostname=self.host, session=self.sock.session)
        return conn, size