↩️ [Back to repository overview](../README.md)

# About
Project subdirectories represent stable units of work meeting clearly defined business needs. At minimum a project has a descriptive name, a primary point of contact, and a README file.

# Standard Project Structure 
```
projects/
└── <project_name>/
    ├── config/
    ├── core/
    ├── data/
    ├── env/
    ├── main.py
    ├── start.ps1
    └── README.md
```

# Standard Project Contents

### `config/`
Configuration for runtime behavior, commonly `.py` and/or `.json` files.

### `core/`
Core business logic, organized in Python modules that will be imported by `main.py`.

### `data/`
Logs, caches, static input data, temporary intermediate data, archived output data, etc.

### `env/`
Environment setup components:

- `conda_env/`: Conda environment for the project (this is excluded from version control and will never be present in the remote repository).
- [`environment.yml`](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually): Defines the environment and version pins dependencies. This will often be used by `setup.ps1` while creating environments.
- `setup.ps1`: PowerShell script that creates `conda_env/`. This should always be used for environment creation to ensure completion of any custom setup.
- [`spec-file.txt`](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#building-identical-conda-environments): Can be used to reproduce an exact `conda_env/` on Windows operating systems.

<sub>*There is significant overlap between environments for existing projects. If deploying from a storage constrained setting in the future (cloud infrastructure for example) it could make sense to build shared environments. Currently storage space is not a factor so the simplicity of isolated project-specific environments is chosen over maximizing storage efficiency.</sub>

### `main.py`
Entry point for execution of all Python code.

### `start.ps1`
PowerShell script that triggers all work done by the project. Handles capture of any stderr output as well as exit code logging.

### `README.md`
A high-level overview of why this project exists, what it does, and any contextual information a new developer would need to effectively maintain it.

# Contacts
| Project                                                  | Primary Point of Contact |
| -------------------------------------------------------- | ------------------------ |
| [ak_parcels](ak_parcels/README.md)                       | connor.edick@alaska.gov  |
| [medevac_runway_search](medevac_runway_search/README.md) | connor.edick@alaska.gov  |
| [regional_kmz_for_ftp](regional_kmz_for_ftp/README.md)   | connor.edick@alaska.gov  |
