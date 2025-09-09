↩️ [Back to repository overview](../../README.md)

↩️ [Back to admin](../README.md)

# About

Two third-party Python libraries are involved in securily storing and accessing sensitive information: [keyring](https://pypi.org/project/keyring/) and [keyrings.cryptfile](https://pypi.org/project/keyrings.cryptfile/)*. These libraries are implemented by [CryptfileKeyringManager](../../library/akdof_shared/src/akdof_shared/security/cryptfile_keyring_manager.py#L28) to standardize how sensitive information is handled across the repository. The approach described below offers multiple layers of protection for sensitive information: 1) Exclusion of sensitive information from version control; 2) Encryption of locally persisting sensitive information using an [industry standard cryptographic algorithm](); 3) Protection of the cryptfile master password using Windows Credential Manager. However, determining what information to consider "sensitive", and securing this information by following the established protocol, is a developer responsibility.

<sub>*`keyrings.cryptfile` is an encrypted file backend for the `keyring` library. All `keyring` backends use the same interface, defined by [keyring.backend.KeyringBackend](https://github.com/jaraco/keyring/blob/main/keyring%2Fbackend.py#L65). This means the approach to storing and accessing sensitive information that is described below could be implemented using a different backend, with very few changes being required in the current `CryptfileKeyringManager` class.</sub> 

# Protocol

## ProjectSecret

Sensitive information is declared using a [ProjectSecret](../../library/akdof_shared/src/akdof_shared/security/cryptfile_keyring_manager.py#L10). The only time that a `ProjectSecret` will have a hard-coded `password` attribute is when a developer is manually saving a new secret to the cryptfile, after which the `password` attribute is removed from code. Once saved, accessing the full `ProjectSecret` at runtime will only require hard-coded `service_name` and `username` attributes. The names of these attributes were chosen to reflect tight coupling with the [keyring core API](https://github.com/jaraco/keyring/blob/main/keyring%2Fcore.py) and don't necessarily describe the contents of what is being saved. At a basic level, `service_name` and `username` are just arbitrary string identifiers that together are used to reference `password`, which is just a piece of sensitive string data. 

## The Cryptfile Master Password

A specific master password is required to access decrypted data from the cryptfile. ***Note that with the `keyrings.cryptfile` library, this password can only be set once per operating system.*** We keep the master password protected in [Windows Credential Manager](https://woshub.com/saved-passwords-windows-credential-manager/), where it is stored and accessed using the keyring library with a [WinVaultKeyring](https://github.com/jaraco/keyring/blob/main/keyring%2Fbackends%2FWindows.py#L65) backend. The only situations when the master password should be present outside of Windows Credential Manager are: During the initial cryptfile configuration process, and during temporary internal sharing over agreed upon secure channels. 

## The Keyring Cryptfile

The cryptfile provides a local file-based backend for the keyring library to use for secret storage and access. We use it instead of the default `WinVaultKeyring` backend for three reasons:
1. Windows Credential Manager has a maximum character length limit that is makes it impossible to store certain types of information there.
2. The cryptfile is easy to share internally among a development team that works from different operating systems.
3. The cryptfile cleanly seperates secret management for the repository from general system level secret management concerns. 

While the contents of the cryptfile are encrypted using industry standard cryptographic algorithms, it is still not something we commit to version control. The cryptfile should only ever exist on your local operating system, and only ever be transferred to team members over agreed upon secure channels.  

## Storage Pattern

## Access Pattern

## Cryptfile Modifications: Please Consult the Team

Contributers should rarely, if ever, need to modify the cryptfile. The internally distributed file is intended to be preconfigured and ready to go for our use cases. If modifications to the cryptfile are required, there should be consultation with the rest of the team, so we can assess whether to redistribute the modified version to everyone. 