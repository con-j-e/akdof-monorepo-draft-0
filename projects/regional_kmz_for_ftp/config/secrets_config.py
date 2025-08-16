import os
from pathlib import Path

from keyring.backends.Windows import WinVaultKeyring

from akdof_shared.security.cryptfile_keyring_manager import CryptfileKeyringManager, ProjectSecret
from akdof_shared.security.api_auth_manager import ArcGisApiAuthManager
from akdof_shared.utils.gmail_sender import GmailSender

CKM = CryptfileKeyringManager(
    master_password_keyring_backend=WinVaultKeyring(),
    master_password_service_name="akdof_monorepo_master_service",
    master_password_username="akdof_monorepo_master_user",
    cryptfile_path=Path(os.getenv("AKDOF_ROOT")) / "admin" / "secrets" / "keyring_cryptfile.cfg"
)

NIFC_FTP_CREDENTIALS = CKM.get_full_secret(ProjectSecret(service_name="ftp.wildfire.gov", username="cedick"))
"""`<ftp_url>, <username>, <password>` for authenticating with ftp.wildfire.gov"""

NIFC_AGOL_CREDENTIALS = CKM.get_full_secret(ProjectSecret(service_name="https://nifc.maps.arcgis.com/", username="AK_State_Authoritative_nifc"))
"""`<portal_url>, <username>, <password>` for authenticating with ArcGIS Online"""

NIFC_ARCGIS_AUTH = ArcGisApiAuthManager(
    cryptfile_keyring_manager=CKM,
    project_secret=NIFC_AGOL_CREDENTIALS
)

NIFC_TOKEN = NIFC_ARCGIS_AUTH.checkout_token(minutes_needed=45)

def gmail_sender_factory() -> GmailSender:
    sender_full_secret = CKM.get_full_secret(
        ProjectSecret(
            service_name="gmail",
            username="akdofscripts@gmail.com"
        )
    )
    recipient_full_secret = CKM.get_full_secret(
        ProjectSecret(
            service_name="send_gmail",
            username="regional_kmz_for_ftp"
        )
    )
    return GmailSender(
        sender_address=sender_full_secret.username,
        sender_app_password=sender_full_secret.password,
        recipient_address=recipient_full_secret.password
    )

GMAIL_SENDER = gmail_sender_factory()