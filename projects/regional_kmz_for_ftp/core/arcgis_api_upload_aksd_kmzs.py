import os
from pathlib import Path
from zipfile import ZipFile

from arcgis.gis import GIS

from akdof_shared.utils.with_retry import with_retry

from config.logging_config import FLM

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

def upload_aksd_kmzs(output_kmz_directory: Path, aksd_kmz_item_ids: dict[str, str], gis: GIS) -> None:

    files_to_delete = list()

    for region, item_id in aksd_kmz_item_ids.items():
        if not os.path.isfile(rf"{output_kmz_directory}/{region}_AKSD.kmz"):
            _LOGGER.error(f"File not found: {region}_AKSD.kmz")
            continue

        props = {
            "type": "KML Collection",
            "dataURL": None,
            "filename": None,
            "typeKeywords": None,
            "description": "This file is updated daily during fire season.",
            "title": f"{region}_AKSD",
            "url": None,
            "text": None,
            "tags": "AKSD_KMZ",
            "snippet": f"Zipped KMZ file of the Alaska Known Sites Database for {region} region.",
            "extent": None,
            "spatialReference": "EPSG:4326",
            "accessInformation": "Data sourced from BLM Alaska Fire Service",
            "licenseInfo": None,
            "culture": None,
            "commentsEnabled": False,
            "overwrite": True,
        }

        kmz_file = output_kmz_directory / f"{region}_AKSD.kmz"
        kmz_zip = output_kmz_directory / f"{region}_AKSD.zip"

        with ZipFile(kmz_zip, "w") as myzip:
            myzip.write(kmz_file, arcname=kmz_file.name)

        def _update_aksd_item():
            item = gis.content.get(item_id)
            success = item.update(item_properties=props, data=str(kmz_zip))
            if success:
                _LOGGER.info(f"{region}_AKSD.kmz update success.")
            else:
                raise RuntimeError(f"{region}_AKSD.kmz (Item ID {item_id}) failed to update.")

        try:
            with_retry(_update_aksd_item, retry_logger=_LOGGER)
        except Exception as e:
            _LOGGER.error(FLM.format_exception(exc_val=e, full_traceback=True))

        files_to_delete.extend([kmz_file, kmz_zip])

    for file in files_to_delete:
        os.remove(file)