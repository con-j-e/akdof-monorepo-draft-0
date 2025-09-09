↩️ [Back to repository overview](../../README.md)

↩️ [Back to admin](../README.md)

# About

Exit code logging provides a generalizable process stability metric that can be used across all projects. Exit codes are formalized by the [ExitStatus](../../library/akdof_shared/src/akdof_shared/protocol/file_logging_manager.py#L19) [IntEnum](https://docs.python.org/3/library/enum.html#enum.IntEnum). Codes  `30`, `40`, and `50` correspond directly to log levels established in the Python [logging](https://docs.python.org/3/library/logging.html) module. Code `1` was arbitrarily chosen for all normal exit circumstances - although it is important that a truthy value is used (instead of `0` which is falsey). This allows us to return from `main()` using a ternary expression, providing an added layer of assurance that an unexpected edge case during our exit logic will still result in a meaningful exit code being logged.*

<sub>*This return pattern is consistent across projects. See an example [here.](../../projects/regional_kmz_for_ftp/main.py#L53)</sub>

# Protocol

Three steps are required for a project to adhere to proper exit code logging:
1. Configure a [FileLoggingManager](../../library/akdof_shared/src/akdof_shared/protocol/file_logging_manager.py#L82) instance and use it for all file logging needs across the project.
2. Use [MainExitManager](../../library/akdof_shared/src/akdof_shared/protocol/main_exit_manager.py#L76) (or [AsyncMainExitManager](../../library/akdof_shared/src/akdof_shared/protocol/main_exit_manager.py#L101), if defining an asynchronous main process) as a context manager for all the core business logic that executes in `main.py`.
3. Trigger all work done by the project with [start.ps1](../../projects/README.md#startps1), which calls [Write-ExitLog](WriteExitLog.psm1#L1) as soon as `main.py` is finished executing.

While team members are encouraged to review the underlying Python and PowerShell modules for a deeper understanding, simply following the previously established usage pattern is sufficient for integrating new projects with the repository. 