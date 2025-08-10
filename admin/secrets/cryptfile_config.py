import os
from pathlib import Path
from typing import Iterable

from keyring.backends.Windows import WinVaultKeyring

from akdof_shared.security.cryptfile_keyring_manager import CryptfileKeyringManager, ProjectSecret

ALL_PROJECT_SECRETS: Iterable[ProjectSecret] = (
    ProjectSecret(
        service_name="https://soa-dnr.maps.arcgis.com/",
        username="for_admin",
        #password=""
    ),
    ProjectSecret(
        service_name="gmail",
        username="akdofscripts@gmail.com",
        #password=""
    ),
    ProjectSecret(
        service_name="send_gmail",
        username="ak_parcels",
        #password=""
    )
)

MANAGER: CryptfileKeyringManager = CryptfileKeyringManager(
    master_password_keyring_backend=WinVaultKeyring(),
    master_password_service_name="akdof_monorepo_master_service",
    master_password_username="akdof_monorepo_master_user",
    cryptfile_path=Path(os.getenv("AKDOF_ROOT")) / "admin" / "secrets" / "keyring_cryptfile.cfg"
)

if __name__ == "__main__":
    pass

    # one-time use
    # choose carefully and store with a trusted password manager
    # an operating system is limited to a single master password for the keyrings.cryptfile library
    # a longer / more complicated password results in more secure encryption
    #MANAGER.store_cryptfile_keyring_master_password(master_password=_)

    # use as-needed
    #MANAGER.store_secrets(project_secrets=ALL_PROJECT_SECRETS)

    # use as-needed
    #MANAGER.delete_secrets(project_secrets=tuple())
