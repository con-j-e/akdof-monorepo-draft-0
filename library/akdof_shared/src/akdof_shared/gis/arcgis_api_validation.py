from typing import Iterable, Literal

import requests


class ArcGisApiErrorResponse(Exception): pass
class ArcGisApiKeyError(Exception): pass

def validate_arcgis_rest_api_json_response(response: requests.Response, expected_keys: str | Iterable[str] | None = None, expected_keys_requirement: Literal["any", "all"] = "any") -> dict:
    """
    Common validation logic for JSON response from ArcGIS REST API

    Parameters
    ----------
    response : requests.Response
        Request response object.
    expected_keys : str | Iterable[str] | None, optional
        Key or keys expected to be in the JSON response, by default None.
    expected_keys_requirement : Literal[&quot;any&quot;, &quot;all&quot;], optional
        Condition on which JSON response is evaluated against expected keys.
        A response with "any" expected key present is considered valid, or a response with "all" expected keys present is considered valid.
        The default is "any".

    Returns
    -------
    dict
        JSON formatted response.

    Raises
    ------
    HTTPError
        Raised by `response.raise_for_status()`.
    JSONDecodeError
        Raised by `response.json()`.
    ArcGisApiErrorResponse
        JSON response contained an 'error' key, indicating an improper request was made by the client.
    ArcGisApiKeyError
        An expected key or keys specified by the caller did not pass the callers expected keys requirement for the JSON response.
    """
    response.raise_for_status()
    json_response = response.json()
    validate_arcgis_json(json_response=json_response, expected_keys=expected_keys, expected_keys_requirement=expected_keys_requirement)
    return json_response

def validate_arcgis_json(json_response: dict, expected_keys: str | Iterable[str] | None = None, expected_keys_requirement: Literal["any", "all"] = "any"):

    if "error" in json_response:
        raise ArcGisApiErrorResponse(f"{json_response}")
    
    if expected_keys:
        expected_keys = (expected_keys,) if isinstance(expected_keys, str) else expected_keys
        if expected_keys_requirement == "any" and not any(key in json_response for key in expected_keys):
            raise ArcGisApiKeyError(f"None of the expected keys {expected_keys} were found in the response: {json_response}")
        elif expected_keys_requirement == "all" and not all(key in json_response for key in expected_keys):
            raise ArcGisApiKeyError(f"One of more of the expected keys {expected_keys} were not found in the response: {json_response}")