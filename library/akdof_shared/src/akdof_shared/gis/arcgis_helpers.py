from pathlib import Path
import uuid

import requests

from akdof_shared.gis.arcgis_api_validation import validate_arcgis_rest_api_json_response
from akdof_shared.utils.drop_none_vals import drop_none_vals


NO_CACHE_HEADERS: dict[str, str] = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}
"""
To be used with GET requests that have the potential to break internal logic if cached responses are allowed.
Note that headers alone are not adequate to prevent caching of responses from ArcGIS REST APIs.
A `{"nocache": uuid.uuid4().hex}` parameter should be passed with the request when the client wants to avoid all caching.
""" 

def get_feature_layer_resource_info(base_url: str, token: str | None = None, verify: Path | bool = True) -> dict:
    """Retrieve comprehensive information about an ArcGIS Online feature layer resource"""

    layer_info_params = drop_none_vals({
        "f": "json",
        "nocache": uuid.uuid4().hex,
        "token": token
    })

    layer_info_response = requests.get(
        url=base_url,
        params=layer_info_params,
        headers=NO_CACHE_HEADERS,
        verify=verify
    )
    layer_info_json = validate_arcgis_rest_api_json_response(response=layer_info_response)

    return layer_info_json

def get_feature_count_and_extent(
        base_url: str,
        where: str = "1=1",
        token: str | None = None,
        out_sr: int | None = None,
        spatial_query_params: dict | None = None,
        verify: Path | bool = True
    ) -> tuple[int, dict]:
    """Perform ArcGIS REST API query operation on hosted feature layer to count the number of features and determine the extent of the counted features."""

    get_count_and_extent_params = drop_none_vals({
        "f": "json",
        "returnCountOnly": "true",
        "returnExtentOnly": "true",
        "outSR": out_sr,
        "where": where,
        "nocache": uuid.uuid4().hex,
        "token": token,
        **(spatial_query_params or dict())
    })

    count_and_extent_response = requests.get(
        url=f"{base_url}/query?",
        params=get_count_and_extent_params,
        headers=NO_CACHE_HEADERS,
        verify=verify
    )
    count_and_extent_json = validate_arcgis_rest_api_json_response(response=count_and_extent_response, expected_keys=("count","extent"), expected_keys_requirement="all")

    return (count_and_extent_json["count"], count_and_extent_json["extent"])

def get_object_ids(
        base_url: str,
        where: str = "1=1",
        token: str | None = None,
        spatial_query_params: dict | None = None,
        verify: Path | bool = True
    ) -> list[int]:
    """Perform ArcGIS REST API query operation on hosted feature layer to retrieve Object IDs of features."""

    get_oids_params = drop_none_vals({
        "f": "json",
        "returnIdsOnly": "true",
        "where": where,
        "nocache": uuid.uuid4().hex,
        "token": token,
        **(spatial_query_params or dict())
    })

    oids_response = requests.get(
        url=f"{base_url}/query?",
        params=get_oids_params,
        headers=NO_CACHE_HEADERS,
        verify=verify
    )
    oids_json = validate_arcgis_rest_api_json_response(response=oids_response, expected_keys="objectIds")

    return oids_json["objectIds"]
            
def expand_envelope(envelope: dict, expansion_distance: int) -> dict:
    """
    Modify an ArcGIS json [envelope](https://developers.arcgis.com/rest/services-reference/enterprise/geometry-objects/#envelope) in-place by expanding it in all directions by the specified expansion distance.
    This distance value is interpreted in the envelopes native CRS.
    """
    for coord, value in envelope.items():
        if "max" in coord:
            envelope[coord] = value + expansion_distance
        elif "min" in coord:
            envelope[coord] = value - expansion_distance
    return envelope


def create_envelope_around_point(arcgis_point_geometry: dict, expansion_distance: int) -> dict:
    """
    Create an ArcGIS json [envelope](https://developers.arcgis.com/rest/services-reference/enterprise/geometry-objects/#envelope) around point coordinates by moving the point coordinates in all directions by the specified expansion distance.
    This distance value is interpreted in the points native CRS.
    """
    x, y = arcgis_point_geometry["x"], arcgis_point_geometry["y"]
    envelope = {
        "xmin": x - expansion_distance,
        "ymin": y - expansion_distance,
        "xmax": x + expansion_distance,
        "ymax": y + expansion_distance,
    }
    return envelope