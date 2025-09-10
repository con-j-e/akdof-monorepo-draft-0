"""A one-time-use script intended for manual execution by a team member who is configuring the cryptfile keyring for the first time."""

import os
from pathlib import Path

from keyring.backends.Windows import WinVaultKeyring

from akdof_shared.security.cryptfile_keyring_manager import CryptfileKeyringManager

CKM = CryptfileKeyringManager(
    master_password_keyring_backend=WinVaultKeyring(),
    master_password_service_name="akdof_monorepo_master_service",
    master_password_username="akdof_monorepo_master_user",
    cryptfile_path=Path(os.getenv("AKDOF_ROOT")) / "admin" / "secrets" / "keyring_cryptfile.cfg"
)
"""Central keyring manager for encrypted credential storage."""

CRYPTFILE_MASTER_PASSWORD: str | None = None
"""
Master password that can decrypt information in the cryptfile.
Please read [documentation](https://github.com/con-j-e/akdof-monorepo-draft-0/tree/main/admin/secrets#the-cryptfile-master-password) for further context.
"""

if __name__ == "__main__":
    assert CRYPTFILE_MASTER_PASSWORD is not None, "assign the master password (as a string) to `CRYPTFILE_MASTER_PASSWORD`."
    CKM.store_cryptfile_keyring_master_password(master_password=CRYPTFILE_MASTER_PASSWORD)