import os
from pathlib import Path
from typing import Iterable

from keyring.backends.Windows import WinVaultKeyring

from akdof_shared.security.cryptfile_keyring_manager import CryptfileKeyringManager, ProjectSecret

CKM: CryptfileKeyringManager = CryptfileKeyringManager(
    master_password_keyring_backend=WinVaultKeyring(),
    master_password_service_name="akdof_monorepo_master_service",
    master_password_username="akdof_monorepo_master_user",
    cryptfile_path=Path(os.getenv("AKDOF_ROOT")) / "admin" / "secrets" / "keyring_cryptfile.cfg"
)

ALL_PROJECT_SECRETS: Iterable[ProjectSecret] = (
    ProjectSecret(
        service_name="https://soa-dnr.maps.arcgis.com/",
        username="for_admin",
        #password=_
    ),
    ProjectSecret(
        service_name="https://nifc.maps.arcgis.com/",
        username="AK_State_Authoritative_nifc",
        #password=_
    ),
    ProjectSecret(
        service_name="ftp.wildfire.gov",
        username="cedick",
        #password=_
    ),
    ProjectSecret(
        service_name="gmail",
        username="akdofscripts@gmail.com",
        #password=_
    ),
    ProjectSecret(
        service_name="send_gmail",
        username="ak_parcels",
        #password=_
    ),
    ProjectSecret(
        service_name="send_gmail",
        username="regional_kmz_for_ftp",
        #password=_
    )
)

ADD_PROJECT_SECRETS: Iterable[ProjectSecret] = (

)

DELETE_PROJECT_SECRETS: Iterable[ProjectSecret] = (

)

if __name__ == "__main__":
    pass

    # one-time use
    # choose carefully and store with a trusted password manager
    # an operating system is limited to a single master password for the keyrings.cryptfile library
    # a longer / more complicated password results in more secure encryption
    #CKM.store_cryptfile_keyring_master_password(master_password=_)

    # use as-needed
    #CKM.store_secrets(project_secrets=ADD_PROJECT_SECRETS)

    # use as-needed
    #CKM.delete_secrets(project_secrets=DELETE_PROJECT_SECRETS)
