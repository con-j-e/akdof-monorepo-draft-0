"""A use-as-needed script intended for manual execution by a team member who is deleting secrets from the cryptfile."""

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

DELETE_PROJECT_SECRETS: ProjectSecret | Iterable[ProjectSecret] = ()
"""
Secrets to delete from the cryptfile.
Only the `service_name` and `username` attributes of a `ProjectSecret` are required for deletions. 
Please manually update [current_project_secrets_config.py](https://github.com/con-j-e/akdof-monorepo-draft-0/blob/main/admin/secrets/current_project_secrets_config.py)
after deleting secrets.
"""

if __name__ == "__main__":
    assert DELETE_PROJECT_SECRETS, "Please specify a `ProjectSecret` (or an iterable of `ProjectSecret`s) that you would like to delete."
    CKM.delete_secrets(project_secrets=DELETE_PROJECT_SECRETS)
