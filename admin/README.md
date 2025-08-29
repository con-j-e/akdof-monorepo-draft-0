↩️ [Back to repository overview](../README.md)

## About
A directory for resources and configuration used to administer projects. 

### `certs/`
Resources for SSL verification on the State of Alaska network.
The `root/` subdirectory contains the Zscaler root certificate.
The `chain/` subdirectory contains certificate chains that can be used for SSL verification with specific HTTPS endpoints.
All certificate chains are expected to use the naming convention `{host}:{port}_chain.pem`.
See `certs/README.md` for instructions on creating certificate chains.

### `env/`
Conda environment used for admin purposes. See `env` description in `projects/README.md` for details.

### `exit_log/`
It is expected that `start.ps1` in every project imports from `exit_log/WriteExitLog.psm1` to write a log message to `exit_log/exit_log.csv`.

### `secrets/`
Encrypted secret store and a Python script for configuring encrypted secrets that projects depend on at runtime. 

### `tasks/`
`TaskSchedule.psm1` defines the configuration for all tasks that are scheduled across the repository.

`RegisterProjectTasks.ps1` registers tasks from `TaskSchedule.psm1` with the operating system.