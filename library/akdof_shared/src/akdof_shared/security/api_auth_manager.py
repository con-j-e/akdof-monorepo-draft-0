from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime as dt, timezone as tz, timedelta
from pathlib import Path
import time

import keyring
import requests

from akdof_shared.gis.arcgis_api_validation import validate_arcgis_rest_api_json_response
from akdof_shared.protocol.datetime_info import iso_from_timestamp, datetime_from_iso, valid_iso_datetime

from akdof_shared.security.cryptfile_keyring_manager import ProjectSecret, CryptfileKeyringManager, PasswordNotFound

class InvalidTimedTokenFormat(Exception): pass

@dataclass(frozen=True)
class TimedToken:
    """
    Attributes
    ----------
    token : str
        API access token
    expiration_time : str
        Token expiration time as an ISO 8601 formatted string
    """
    token: str
    expiration_time: str
    
    def __post_init__(self):
        if "||" in self.token:
            raise InvalidTimedTokenFormat(f"Cannot support '||' character sequence in token (reserved for TimedToken __str__ method)")
        if not valid_iso_datetime(iso_datetime=self.expiration_time):
            raise InvalidTimedTokenFormat(f"{self.expiration_time} is not a valid ISO 8601 string")
    
    def __str__(self):
        return f"{self.token}||{self.expiration_time}"
    
    @property
    def lifespan(self) -> timedelta:
        return datetime_from_iso(self.expiration_time) - dt.now(tz.utc)

class ApiAuthManager(ABC):
    """
    Abstract base class for managing API authentication

    Class Attributes
    ----------
    auth_url : str
        URL endpoint to use for token generation requests

    Instance Attributes
    ----------
    cryptfile_keyring_manager : CryptfileKeyringManager
        Must already be configured with a cryptfile and master password
    project_secret : ProjectSecret
        Must already be stored with the configured `cryptfile_keyring_manager`
    ssl_cert_chain : Path | None
        Certificate chain to use for SSL verification, by default None
    """    
    auth_url = ""

    def __init__(
        self,
        cryptfile_keyring_manager: CryptfileKeyringManager,
        project_secret: ProjectSecret,
        ssl_cert_chain: Path | None = None
    ):
        self.cryptfile_keyring_manager = cryptfile_keyring_manager
        self.project_secret = project_secret
        self.ssl_cert_chain = ssl_cert_chain

        self.cryptfile_keyring_manager._lazy_set_cryptfile_keyring()

    def checkout_token(self, minutes_needed: int) -> str:
        """
        Check out an existing token, or if necessary generate a new token

        Parameters
        ----------
        minutes_needed : int
            How long token will be needed for. Underestimating may result in token expiring during use.

        Returns
        -------
        str
            Token
        """
        previous_token = keyring.get_password(self.project_secret.service_name, "__TimedToken__")

        if previous_token is None:
            timed_token = self._generate_token()
            keyring.set_password(self.project_secret.service_name, "__TimedToken__", f"{timed_token}")
        else:
            token, expiration_time = previous_token.split("||")
            timed_token = TimedToken(token, expiration_time)
            if timed_token.lifespan < timedelta(seconds=abs(minutes_needed) * 60):
                timed_token = self._generate_token()
                keyring.set_password(self.project_secret.service_name, "__TimedToken__", f"{timed_token}")

        return timed_token.token

    @abstractmethod
    def _generate_token(self) -> TimedToken:
        raise NotImplementedError("`ApiAuthManager` subclasses must define their own _generate_token() method.")

class ArcGisApiAuthManager(ApiAuthManager):
    """
    Manages ArcGIS REST API authentication

    Must be initialized with a `ProjectSecret` having the following format:
        `ProjectSecret.service_name` = url of client application that will use the token (for example, 'https://nifc.maps.arcgis.com')
        `ProjectSecret.username` = username for account requesting the token
        `ProjectSecret.password` = password for account requesting the token
    """

    auth_url: str = "https://www.arcgis.com/sharing/rest/generateToken"

    def _generate_token(self) -> TimedToken:

        service_name, username = self.project_secret.service_name, self.project_secret.username
        password = keyring.get_password(service_name, username)
        if password is None:
            raise PasswordNotFound(f"No cryptfile keyring password found for {service_name, username}")

        response = requests.post(
            url=self.auth_url,
            data={
                "username": username,
                "password": password,
                "referer": service_name,
                "client": "referer",
                "f": "json",
            },
            verify=self.ssl_cert_chain or True
        )
        json_response = validate_arcgis_rest_api_json_response(response=response, expected_keys=("token","expires"), expected_keys_requirement="all")

        return TimedToken(
            token=json_response["token"],
            expiration_time=iso_from_timestamp(epoch=json_response["expires"], epoch_units="milliseconds")
        )
    
class SentinelApiAuthManager(ApiAuthManager):
    """
    Manages Sentinel Hub REST API authentication

    Must be initialized with a `ProjectSecret` having the following format:
        `ProjectSecret.service_name` = any
        `ProjectSecret.username` = any
        `ProjectSecret.password` = `f"{client_id}||{client_secret}"`
    """

    auth_url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"

    def _generate_token(self) -> TimedToken:
   
        service_name, username = self.project_secret.service_name, self.project_secret.username
        client_id_and_secret = keyring.get_password(service_name, username)
        if client_id_and_secret is None:
            raise PasswordNotFound(f"No cryptfile keyring password found for {service_name, username}")
        client_id, client_secret = client_id_and_secret.split("||")

        response = requests.post(
            url=self.auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            verify=self.ssl_cert_chain or True
        )
        response.raise_for_status()
        data = response.json()

        return TimedToken(
            token=data["access_token"],
            expiration_time=iso_from_timestamp(epoch=(time.time() + data["expires_in"]))
        )