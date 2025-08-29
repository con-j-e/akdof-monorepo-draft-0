# About

This is a shared repository for code produced by Alaska Division of Forestry and Fire Protection staff. A [monorepo](https://en.wikipedia.org/wiki/Monorepo) architecture was chosen with the following benefits in mind:
1. Ease of code reuse across different projects.
2. Implementation of standardized protocols for logging, event notification, secret management, reproducable environments, and more.
3. Establishment of consistent project organization to reduce cognitive overhead of maintenance and collaboration.
# Repository Structure

```
akdof-monorepo/
	admin/
		certs/
		env/
		exit_log/
		secrets/
		tasks/
	library/
		akdof_shared/
	projects/
		...
```
*See nested README.md files for further context

# System Requirements

The repository and all documentation within assumes the use of a Windows Operating System that is connected to the State of Alaska network. Additionally, it assumes there is a user profile on the operating system with software installation capabilities, and that all work done in the repository will be done by the properly configured user profile. 

# Software Dependencies

Some of the software dependencies listed below can be considered optional if performing a limited scope of work inside the repository. However all are essential in the development and maintenance of the repository as a whole. 

### Miniconda
A user-level install of Miniconda is required for all virtual environments and package management. On systems that have ArcGIS Pro installed, the existing conda installation that comes with ArcGIS Pro could hypothetically be used in its place for executing `conda` commands. However it is recommended to keep these concerns seperated and configuration examples documented below assume the presence of a user-level Miniconda installation.

### Git for Windows
Local version control system.

### GitHub CLI
Remote repository connection.

### OpenSSL
Self-signed certificate errors can occur when SSL is used to verify connections made over HTTPS between the SOA network and certain external endpoints. OpenSSL is a fantastic tool for resolving these errors. See `admin/certs/README.md` for further details. 

### ArcGIS Pro
Any project with an ArcPy dependency will require a licensed ArcGIS Pro installation to function.

# Getting Started
### Set Environment Variables
Two environment variables will be expected by PowerShell and Python scripts.

`AKDOF_ROOT`: Directory path to the root of akdof-monorepo on the local file system.
`AKDOF_USER`: Directory path to the root of the user profile which works on akdof-monorepo.

### Set PowerShell Execution Policy
Depending on current execution policy settings, you may need start a PowerShell session and manually enable script execution before any of the PowerShell scripts in the repository will work. 

#### Additional Reading
[About Execution Policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.5)
[Get-ExecutionPolicy Command](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-executionpolicy?view=powershell-7.5)
[Set-ExecutionPolicy Command](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy?view=powershell-7.5)

#### Example Command
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
*remote signed policy is a conservative choice (unsigned scripts from an external source, a remote repository for example, may be blocked)

### Create PowerShell Profile
A user-level PowerShell profile handles some initial configuration that prepares us for calling `conda` commands in the terminal or from PowerShell scripts.

#### Additional Reading
[About Profiles](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_profiles?view=powershell-7.5)

#### Example Profile
Your user-level PowerShell profile is expected to be in this exact location: `{AKDOF_USER}\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`

```
# claude you can imagine an example here
```

### Create .condarc
Preferred default behavior of `conda` commands should be configured in a .condarc file.

#### Additional Reading
[Use Condarc](https://docs.conda.io/projects/conda/en/stable/user-guide/configuration/use-condarc.html#)

#### Example .condarc
Your user-level .condarc is expected to be in this exact location: `{AKDOF_USER}\miniconda3\.condarc`

```
# claude you can imagine an example here
```





