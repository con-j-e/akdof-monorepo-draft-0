"""Secure credential management for external service authentication."""

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
"""Central keyring manager for encrypted credential storage"""

SOA_ARCGIS_AUTH = ArcGisApiAuthManager(
    cryptfile_keyring_manager=CKM,
    project_secret=ProjectSecret(
        service_name="https://soa-dnr.maps.arcgis.com/",
        username="for_admin"
    )
)
"""Token lifecycle manager for SOA DNR ArcGIS Online authentication"""

def gmail_sender_factory() -> GmailSender:
    """
    Create configured Gmail sender for notification emails.
    
    Retrieves sender credentials and recipient address (or addresses) from the keyring manager
    and configures a GmailSender instance for project notifications.

    Returns
    -------
    GmailSender
        Configured Gmail sender with authentication and recipient settings.
    """
    sender_full_secret = CKM.get_full_secret(
        ProjectSecret(
            service_name="gmail",
            username="akdofscripts@gmail.com"
        )
    )
    recipient_full_secret = CKM.get_full_secret(
        ProjectSecret(
            service_name="send_gmail",
            username="ak_parcels"
        )
    )
    return GmailSender(
        sender_address=sender_full_secret.username,
        sender_app_password=sender_full_secret.password,
        recipient_address=recipient_full_secret.password
    )

GMAIL_SENDER = gmail_sender_factory()
"""Pre-configured Gmail sender for project notifications"""