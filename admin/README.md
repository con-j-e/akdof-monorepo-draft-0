↩️ [Back to repository overview](../README.md)

# About
A directory for resources and configuration used to administer projects.

# Contents
### `certs/`
Resources for SSL verification on the State of Alaska network. Further context [here](certs/README.md).

### `env/`
Conda environment, used for admin purposes. See `env/` description [here](../projects/README.md) for details.

### `exit_log/`
Exit code log file and an exit code logging module that get used by all projects.

### `secrets/`
Encrypted secret store and a Python script for configuring encrypted secrets.

### `tasks/`
`TaskSchedule.psm1` defines the configuration for all tasks that are scheduled across the repository.

`RegisterProjectTasks.ps1` registers tasks from `TaskSchedule.psm1` with the operating system.