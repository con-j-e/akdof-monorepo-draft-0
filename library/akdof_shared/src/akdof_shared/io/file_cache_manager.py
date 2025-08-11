
from datetime import datetime as dt, timezone as tz, timedelta
from enum import Enum
from typing import Iterable, Literal, Protocol
from pathlib import Path
from itertools import islice

from akdof_shared.protocol.datetime_info import datetime_from_iso, iso_file_parsing

class BadCacheFileName(Exception): pass
class CacheCompareError(Exception): pass
class ViolatedFileExtensionRule(Exception): pass

class CacheManifest(dict[Path, dt]):
    """A dictionary of { valid file cache path : UTC creation datetime } pairs, sorted by creation datetime in descending order"""

    def __init__(self, raw_dict: dict[Path, dt]):

        for file_path, creation_dt in raw_dict.items():
            if not isinstance(file_path, Path):
                raise TypeError(f"Keys must be Path, got {type(file_path)}")
            if not file_path.exists():
                raise FileNotFoundError(f"Path does not exist: {file_path}")
            if not file_path.is_file():
                raise ValueError(f"Path must be a file, not a directory: {file_path}")
            if not isinstance(creation_dt, dt):
                raise TypeError(f"Values must be datetime, got {type(creation_dt)}")
            if creation_dt.tzinfo is None or creation_dt.tzinfo != tz.utc:
                raise ValueError("Creation datetimes for file cache paths must be timezone-aware UTC datetimes")
            
        sorted_paths = sorted(raw_dict, key=raw_dict.get, reverse=True)
        sorted_path_dt_pairs = {file_path: raw_dict[file_path] for file_path in sorted_paths}

        super().__init__(sorted_path_dt_pairs)

class PurgeMethod(Enum):
    ANY_EXPIRED = "any_expired"
    OLDEST_WHILE_MAX_COUNT_EXCEEDED = "oldest_while_max_count_exceeded" 
    BOTH = "both"

class CacheCompareFunc(Protocol):
   def __call__(self, file_a: Path, file_b: Path, output_directory: Path) -> Path | None:
       """
       Perform any comparitive analysis between resource at `file_a` and resource at `file_b`
       and save any output resource in `output_directory`.
       Returns path to output resource or None if no relevant comparison results were generated.
       """
       ...

class FileCacheManager:
    """
    Manages a file cache.

    Attributes:
        path: Descriptively named directory root for a particular file cache
        max_age: How long after creation cached files will be considered expired
        max_count: How many files sharing the same file extension can be in the cache at any one time
        purge_method: Strategy for purging files from the cache
        file_extensions: File extension patterns that will be considered when globbing the cache.
            FileCacheManager instances will treat groupings created by different file extension patterns like different caches.
        cache_compare_func: To be called by compare_latest_entries(), comparing two most recent cache entries for a given file extension
    """
    def __init__(
        self,
        path: Path,
        max_age: timedelta,
        max_count: int,
        purge_method: PurgeMethod = PurgeMethod.BOTH,
        file_extensions: tuple[str] = ("*.json",),
        cache_compare_func: CacheCompareFunc | None = None
    ):
        self.path = path
        self.max_age = max_age
        self.max_count = max_count
        self.purge_method = purge_method
        self.file_extensions = file_extensions
        self.cache_compare_func = cache_compare_func
        
        self.path.mkdir(parents=True, exist_ok=True)
        self._purge_cache()
        for ext in self.file_extensions:
            self._validate_file_extension(ext)

    def load_manifest(self, file_extensions: str | Iterable[str] | Literal["all"] = "all") -> CacheManifest:

        if file_extensions == "all":
            file_extensions = self.file_extensions
        elif isinstance(file_extensions, str):
            file_extensions = (file_extensions,)

        raw_dict = dict()
        for extension in file_extensions:
            self._validate_file_extension(extension)
            for file_path in self.path.glob(extension):
                try:
                    creation_dt = datetime_from_iso(iso_file_parsing(file_path.stem))
                except Exception as e:
                    raise BadCacheFileName(f"Bad file name {file_path.stem} found in cache {self.path}") from e
                raw_dict[file_path] = creation_dt

        return CacheManifest(raw_dict)
        
    def parse_manifest(self, target_length: int, file_extension: str | None = None) -> CacheManifest:

        if file_extension is None and len(self.file_extensions) > 1:
            raise ViolatedFileExtensionRule(f"FileCacheManager for {self.path} specifies multiple `file_extensions` ({self.file_extensions}), so the caller must specify which `file_extension` to pull from the manifest.")
        file_extension = file_extension or self.file_extensions[0]

        manifest = self.load_manifest(file_extensions=file_extension)
        manifest = CacheManifest(dict(islice(manifest.items(), target_length)))

        return manifest

    def latest_entry(self, ignore_expired: bool = True, file_extension: str | None = None) -> Path | None:
        manifest = self.parse_manifest(target_length=1, file_extension=file_extension)
        file_path = next(iter(manifest), None)
        if file_path and ignore_expired:
            creation_dt = manifest[file_path]
            if (dt.now(tz=tz.utc) - creation_dt) > self.max_age:
                return None
        return file_path

    def compare_latest_entries(self, file_extension: str | None = None) -> Path | None:

        if self.cache_compare_func is None:
            raise NotImplementedError(f"FileCacheManager for {self.path} has no `cache_compare_func` attribute!")
        
        manifest = self.parse_manifest(target_length=2, file_extension=file_extension)
        file_paths = list(manifest.keys())
        if len(file_paths) < 2:
            return None
        
        file_extension = file_extension or self.file_extensions[0]
        try:
            return self.cache_compare_func(
                file_a=file_paths[1],
                file_b=file_paths[0],
                output_directory=self.path / f"compare_{file_extension.replace('.','').replace('*','')}"
            )
        except Exception as e:
            raise CacheCompareError(f"FileCacheManager for {self.path} failed to compare cache entries") from e

    def _purge_any_expired(self):
        manifest = self.load_manifest()
        for file_path, creation_dt in manifest.items():
            if (dt.now(tz=tz.utc) - creation_dt) > self.max_age:
                file_path.unlink()

    def _purge_oldest_while_max_count_exceeded(self):
        for extension in self.file_extensions:
            manifest = self.load_manifest(file_extensions=extension)
            while len(manifest) > self.max_count:
                oldest_file_path = min(manifest, key=manifest.get)
                oldest_file_path.unlink()
                del manifest[oldest_file_path]

    def _purge_cache(self):
        if self.purge_method in [PurgeMethod.ANY_EXPIRED, PurgeMethod.BOTH]:
            self._purge_any_expired()
        if self.purge_method in [PurgeMethod.OLDEST_WHILE_MAX_COUNT_EXCEEDED, PurgeMethod.BOTH]:
            self._purge_oldest_while_max_count_exceeded()

    def _validate_file_extension(self, file_extension: str):
        if not file_extension.startswith("*."):
            raise ViolatedFileExtensionRule(f"FileCacheManager for {self.path} got a bad file extension pattern '{file_extension}'. Patterns must start with '*.'")