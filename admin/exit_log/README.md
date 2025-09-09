↩️ [Back to repository overview](../../README.md)

↩️ [Back to admin](../README.md)

# About

Exit code logging provides a generalizable process stability metric that can be used across all projects. Exit codes are formalized by the [ExitStatus](../../library/akdof_shared/src/akdof_shared/protocol/file_logging_manager.py#L19) enum. Codes  `30`, `40`, and `50` correspond directly to log levels established in the Python [logging] module. Code `1` was arbitrarily chosen for all normal exit circumstances - although it is important that a truthy value is used (instead of `0` which is falsey). This gives us a [last line of defense] for documenting unexpected edge cases.

# Protocol

Three steps are required for a project to adhere to proper exit code logging:
1. Configure a [FileLoggingManager] instance and use it for all file logging needs across the project.
2. Use [MainExitManager] (or [AsyncMainExitManager], if defining an asynchronous main process) as a context manager for all the core business logic that executes in [main.py].
3. Trigger all work done by the project with [start.ps1], which calls [Write-ExitLog] as soon as [main.py] is finished executing.

People are encouraged to read and understand the Python and PowerShell modules that compose this protocol, but from a purely implementation standpoint, this should not be necessary.