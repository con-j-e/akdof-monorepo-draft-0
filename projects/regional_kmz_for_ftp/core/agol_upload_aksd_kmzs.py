from pathlib import Path
import requests
from zipfile import ZipFile

from akdof_shared.utils.with_retry import with_retry
from akdof_shared.gis.arcgis_api_validation import validate_arcgis_rest_api_json_response

from config.logging_config import FLM

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

class ItemUpdateFailure(Exception): pass

def agol_upload_aksd_kmzs(output_kmz_directory: Path, aksd_kmz_item_ids: dict[str, str], token: str) -> None:

    files_to_delete = list()

    for region, item_id in aksd_kmz_item_ids.items():
        
        stem = f"{region}_AKSD"

        if not (output_kmz_directory / f"{stem}.kmz").exists():
            _LOGGER.error(f"File not found: {stem}.kmz")
            continue

        kmz_file = output_kmz_directory / f"{stem}.kmz"
        kmz_zip = output_kmz_directory / f"{stem}.zip"

        with ZipFile(kmz_zip, "w") as myzip:
            myzip.write(kmz_file, arcname=kmz_file.name)

        def _update_aksd_item():
            with open(kmz_zip, "rb") as myzip:
                files = {"file": (f"{stem}.zip", myzip, "application/zip")}
                response = requests.post(
                    url=f"https://www.arcgis.com/sharing/rest/content/users/AK_State_Authoritative_nifc/items/{item_id}/update",
                    data={"token": token, "f": "json"},
                    files=files
                )
            response_json = validate_arcgis_rest_api_json_response(response=response, expected_keys=("success", "id"), expected_keys_requirement="all")
            if response_json["success"] is not True:
                raise ItemUpdateFailure(f"Failed to update AKSD KMZ item (id: {item_id}) for {region} region")
            _LOGGER.info(f"{stem}.kmz update success.")

        try:
            with_retry(_update_aksd_item, retry_logger=_LOGGER)
        except Exception as e:
            _LOGGER.error(FLM.format_exception(exc_val=e, full_traceback=True))

        files_to_delete.extend([kmz_file, kmz_zip])

    for file in files_to_delete:
        file.unlink()