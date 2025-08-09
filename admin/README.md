## Initial Setup
./system folder might be absolete

### Software Dependencies
- miniconda
- git for windows
- github cli
- open ssl
- arcgis pro

### PowerShell Execution Policy

### Long File System Paths

### User-Level Environment Variables
- keep these or write everything into the powershell profile?
- perhaps those created in powershell profile should be isolated to what powershell scripts need
- python will rely on those set explicitly here (this might just be AKDOF_ROOT)
- AKDOF_USER makes sense from the standpoint of: verbosity, clear designation of where conda lives, of which profile will orchestrate tasks, of where the required powershell profile lives

### SSL Certificates
- formalize naming convention of .pem files in admin/certs/chain? <host:port>_chain.pem
- fewer env vars required, can construct cert paths based on AKDOF_ROOT
- enforces structure in one step, and is extendible from the start (more certs can be introduced without modifying initial setup)

### Example PowerShell Profile

### Example .condarc