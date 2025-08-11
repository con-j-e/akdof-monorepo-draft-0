from enum import IntEnum

class ExitStatus(IntEnum):
    """
    Status codes that all Python programs run as `__main__` are expected to exit with.
    These codes represent the highest severity level of one or more events that were logged.

    Attributes
    ----------
    OK : 0
        Operations normal.
    WARNING : 30
        Something occurred that is out of the ordinary, or that might indicate a problem.
    ERROR : 40
        A non-critical error occurred. The main program is expected to have continued running.
    CRITICAL : 50
        A critical error occurred. The main program is expected to have terminated prematurely.
    """
    OK = 0
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
