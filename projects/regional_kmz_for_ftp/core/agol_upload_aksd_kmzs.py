from pathlib import Path
import requests
from zipfile import ZipFile

from akdof_shared.utils.with_retry import with_retry
from akdof_shared.gis.arcgis_api_validation import validate_arcgis_rest_api_json_response

from config.logging_config import FLM

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

class ItemUpdateFailure(Exception): 
    """Exception raised if AKSD KMZ item update fails."""
    pass

def agol_upload_aksd_kmzs(output_kmz_directory: Path, aksd_kmz_item_ids: dict[str, str], token: str) -> None:
    """
    Zips Alaska Known Sites Database KMZ files and uploads them to corresponding ArcGIS Online items.
    Successfully uploaded files are moved to an 'agol_complete' subdirectory.
    Missing files and upload failures are logged but do not interrupt processing of remaining items.

    Parameters
    ----------
    output_kmz_directory : Path
        Directory containing the KMZ files to upload.
    aksd_kmz_item_ids : dict[str, str]
        Mapping of region names to ArcGIS Online item IDs.
    token : str
        ArcGIS Online authentication token.
    """
    for region, item_id in aksd_kmz_item_ids.items():

        stem = f"{region}_AKSD"
        kmz_file = output_kmz_directory / f"{stem}.kmz"
        if not kmz_file.exists():
            _LOGGER.error(f"File not found: {kmz_file}")
            continue

        kmz_zip = output_kmz_directory / f"{stem}.zip"
        with ZipFile(kmz_zip, "w") as myzip:
            myzip.write(kmz_file, arcname=kmz_file.name)

        def _update_aksd_item():
            """Update item via ArcGIS REST API."""
            with open(kmz_zip, "rb") as myzip:
                files = {"file": (f"{stem}.zip", myzip, "application/zip")}
                response = requests.post(
                    url=f"https://www.arcgis.com/sharing/rest/content/users/AK_State_Authoritative_nifc/items/{item_id}/update",
                    data={"token": token, "f": "json"},
                    files=files,
                    timeout=30
                )
            response_json = validate_arcgis_rest_api_json_response(response=response, expected_keys=("success", "id"), expected_keys_requirement="all")
            if response_json["success"] is not True:
                raise ItemUpdateFailure(f"Failed to update AKSD KMZ item (id: {item_id}) for {region} region")

        try:
            with_retry(_update_aksd_item, retry_logger=_LOGGER)
            _LOGGER.info(f"{stem}.kmz update success.")
            for path in (kmz_file, kmz_zip):
                path.replace(output_kmz_directory / "agol_complete" / path.name)
        except Exception as e:
            _LOGGER.error(FLM.format_exception(exc_val=e, full_traceback=True))