"""A use-as-needed script intended for manual execution by a team member who is storing secrets in the cryptfile."""

import os
from pathlib import Path
from typing import Iterable

from keyring.backends.Windows import WinVaultKeyring

from akdof_shared.security.cryptfile_keyring_manager import CryptfileKeyringManager, ProjectSecret

CKM = CryptfileKeyringManager(
    master_password_keyring_backend=WinVaultKeyring(),
    master_password_service_name="akdof_monorepo_master_service",
    master_password_username="akdof_monorepo_master_user",
    cryptfile_path=Path(os.getenv("AKDOF_ROOT")) / "admin" / "secrets" / "keyring_cryptfile.cfg"
)
"""Central keyring manager for encrypted credential storage."""

STORE_PROJECT_SECRETS: ProjectSecret | Iterable[ProjectSecret] = ()
"""
Secrets to store in the cryptfile. All attributes of a `ProjectSecret` are required for storage.
This constant can specify existing secrets that need their `password` attribute updated,
or entirely new secrets. If storing entirely new secrets,
please manually update [current_project_secrets_config.py](https://github.com/con-j-e/akdof-monorepo-draft-0/blob/main/admin/secrets/current_project_secrets_config.py)
afterward.
"""

if __name__ == "__main__":
    assert STORE_PROJECT_SECRETS, "Please specify a `ProjectSecret` (or an iterable of `ProjectSecret`s) that you would like to store."
    CKM.store_secrets(project_secrets=STORE_PROJECT_SECRETS)
