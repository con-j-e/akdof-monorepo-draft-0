"""
These functions exist to support the consistent representation of date and time information at runtime and when saving to persistent state.
ISO 8601 formatted strings are preferred in all cases except when the functionality of datetime objects is being used for some operation.
All date and time information must explicitly be in UTC.
"""

from datetime import datetime as dt
from datetime import timezone as tz
from typing import Literal

class NoTimezoneError(Exception): pass

def enforce_utc(dt_obj: dt) -> dt:
    """Ensures datetime object is timezone-aware and in UTC"""
    if dt_obj.tzinfo is None:
        raise NoTimezoneError("Datetime objects without timezone information are not accepted")
    elif dt_obj.tzinfo != tz.utc:
        dt_obj = dt_obj.astimezone(tz.utc)
    return dt_obj

def datetime_from_iso(iso_format: str) -> dt:
    """Construct a timezone-aware UTC datetime object from a string in ISO 8601 format"""
    return enforce_utc(dt.fromisoformat(iso_format))

def iso_from_datetime(
    dt_obj: dt,
    iso_time_spec: Literal["auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"] = "milliseconds",
) -> str:
    """Construct an ISO 8601 formatted string in UTC from a timezone-aware datetime object"""
    return enforce_utc(dt_obj).isoformat(timespec=iso_time_spec)

def iso_from_timestamp(
    epoch: int | float,
    epoch_units: Literal["seconds", "milliseconds"] = "seconds",
    iso_time_spec: Literal["auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"] = "milliseconds"
) -> str:
    """Construct an ISO 8601 formatted string from an epoch timestamp. Epoch timestamps are assumed to always be in UTC."""
    assert epoch_units in ("seconds", "milliseconds"), "`epoch_units` argument must be either 'seconds' or 'milliseconds'"
    divisor = 1000 if epoch_units == "milliseconds" else 1
    dt_obj = dt.fromtimestamp(epoch / divisor, tz.utc)
    return dt_obj.isoformat(timespec=iso_time_spec)

def now_utc_iso(
    iso_time_spec: Literal["auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"] = "milliseconds"
) -> str:
    """Construct an ISO 8601 formatted string in UTC for the present date and time"""
    return dt.now(tz.utc).isoformat(timespec=iso_time_spec)

def iso_file_naming(iso_format: str) -> str:
    """Convert ISO 8601 string to filesystem-safe format (colons → hyphens , +00:00 → Z)"""
    return iso_format.replace("+00:00", "Z").replace(":", "-")

def iso_file_parsing(filename_format: str) -> str:
    """Convert filesystem-safe format back to ISO 8601 string"""
    result = filename_format.replace("Z", "+00:00")
    if 'T' in result:
        date_part, time_part = result.split('T', 1)
        time_part = time_part.replace('-', ':')
        result = f"{date_part}T{time_part}"
    return result

def valid_iso_datetime(iso_datetime: str | None, nullable: bool = False) -> bool:
    """Boolean validator for ISO 8601 datetime strings"""
    if nullable and iso_datetime is None:
        return True
    try:
        datetime_from_iso(iso_datetime)
        return True
    except Exception:
        return False