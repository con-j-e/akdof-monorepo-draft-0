from pathlib import Path
from typing import Iterable, NamedTuple

import keyring
import keyring.backend
from keyrings.cryptfile.cryptfile import CryptFileKeyring

class PasswordNotFound(Exception): pass

class ProjectSecret(NamedTuple):
    """
    A unit of sensitive information that a project depends on

    Attributes are the exact arguments for `keyring.set_password()`

    It is expected that `service_name` and `username` will remain hard-coded, for securely accessing `password`

    Attributes
    ----------
    service_name : str 
    username : str
    password : str, by default ""
    """    
    service_name: str
    username: str
    password: str = ""

class CryptfileKeyringManager:
    """Implements `keyring` and `keyrings.cryptfile` libraries to manage creation, deletion, and access of sensitive information"""

    def __init__(
        self,
        master_password_keyring_backend: keyring.backend.KeyringBackend,
        master_password_service_name: str,
        master_password_username: str,
        cryptfile_path: Path
    ):
        self.master_password_keyring_backend = master_password_keyring_backend
        self.master_password_service_name = master_password_service_name
        self.master_password_username = master_password_username
        self.cryptfile_path = cryptfile_path

        self.has_cryptfile_keyring_set = False

    def store_cryptfile_keyring_master_password(self, master_password: str):
        """One-time use method for setting the cryptfile keyring master password."""
        keyring.set_keyring(self.master_password_keyring_backend)
        keyring.set_password(self.master_password_service_name, self.master_password_username, master_password)
        print(
            f"Cryptfile keyring master password for `{self.master_password_service_name, self.master_password_username}` stored successfully using backend `{self.master_password_keyring_backend}`"
        )

    def set_cryptfile_keyring(self):
        """Access the cryptfile keyring master password and use it to set the cryptfile keyring"""
        keyring.set_keyring(self.master_password_keyring_backend)
        master_password = keyring.get_password(self.master_password_service_name, self.master_password_username)
        if master_password is None:
            raise PasswordNotFound(
                f"No password found for `{self.master_password_service_name, self.master_password_username}` in backend `{self.master_password_keyring_backend}`"
            )
        kr = CryptFileKeyring()
        kr.keyring_key = master_password
        kr.file_path = self.cryptfile_path
        keyring.set_keyring(kr)
        self.has_cryptfile_keyring_set = True

    def store_secrets(self, project_secrets: Iterable[ProjectSecret] | ProjectSecret):
        """Store secrets using the cryptfile keyring"""
        self._lazy_set_cryptfile_keyring()
        project_secrets = (project_secrets,) if isinstance(project_secrets, ProjectSecret) else project_secrets
        for secret in project_secrets:
            keyring.set_password(*secret)
            print(f"Password set for {secret.service_name, secret.username}")

    def delete_secrets(self, project_secrets: Iterable[ProjectSecret] | ProjectSecret):
        """Delete secrets from the cryptfile keyring"""
        self._lazy_set_cryptfile_keyring()
        project_secrets = (project_secrets,) if isinstance(project_secrets, ProjectSecret) else project_secrets
        for secret in project_secrets:
            keyring.delete_password(secret.service_name, secret.username)
            print(f"Password deleted for {secret.service_name, secret.username}")

    def get_full_secret(self, project_secret: ProjectSecret) -> ProjectSecret:
        """Retrieves `service_name`, `user_name`, and `password` for a project secret"""
        self._lazy_set_cryptfile_keyring()
        service_name, username = project_secret.service_name, project_secret.username
        password = keyring.get_password(service_name, username)
        if password is None:
            raise PasswordNotFound(f"No cryptfile keyring password found for {service_name, username}")
        return ProjectSecret(service_name, username, password)
    
    def _lazy_set_cryptfile_keyring(self):
        """Set the cryptfile keyring if it has not already been set for the calling `CryptfileKeyringManager` instance"""
        if not self.has_cryptfile_keyring_set:
            self.set_cryptfile_keyring()