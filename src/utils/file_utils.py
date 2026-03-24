import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FolderInfo:
    """Stores folder metadata for efficient caching."""
    name: str
    path: str
    ctime: float  # creation time

    def __lt__(self, other):
        return self.ctime > other.ctime  # Sort by newest first


class FolderScanner:
    """
    Optimized folder scanner using os.scandir() for better performance.
    Avoids repeated stat calls by fetching metadata during directory scan.
    """

    def __init__(self, base_path: str):
        self.base_path = base_path
        self._cache: Optional[List[FolderInfo]] = None
        self._cache_path: Optional[str] = None

    def scan_folders(self, use_cache: bool = True) -> List[FolderInfo]:
        """
        Scan directories and return folder info with creation times.
        Uses caching to avoid repeated filesystem calls.
        """
        if use_cache and self._cache is not None and self._cache_path == self.base_path:
            return self._cache

        folders = []
        try:
            # Use os.scandir() for efficient directory iteration
            # scandir caches stat info in the DirEntry object
            with os.scandir(self.base_path) as entries:
                for entry in entries:
                    try:
                        # is_dir() does not follow symlinks and caches the result
                        if entry.is_dir(follow_symlinks=False):
                            # Get stat info - st_ctime is cached by scandir
                            stat_info = entry.stat(follow_symlinks=False)
                            folders.append(FolderInfo(
                                name=entry.name,
                                path=entry.path,
                                ctime=stat_info.st_ctime
                            ))
                    except (OSError, PermissionError):
                        # Skip folders we can't access
                        continue
        except (OSError, PermissionError):
            return []

        # Sort by creation time (newest first)
        folders.sort()

        # Cache the result
        self._cache = folders
        self._cache_path = self.base_path

        return folders

    def get_folder_names(self, use_cache: bool = True) -> List[str]:
        """Get just the folder names, sorted by creation time."""
        return [f.name for f in self.scan_folders(use_cache=use_cache)]

    def filter_folders(self, search_term: str, use_cache: bool = True) -> List[str]:
        """
        Filter folders by search term (case-insensitive substring match).
        Returns folder names sorted by creation time.
        """
        if not search_term:
            return self.get_folder_names(use_cache=use_cache)

        search_lower = search_term.lower()
        all_folders = self.scan_folders(use_cache=use_cache)

        # Filter and maintain the sorted order
        filtered = [f for f in all_folders if search_lower in f.name.lower()]
        return [f.name for f in filtered]

    def invalidate_cache(self):
        """Invalidate the folder cache when directory contents may have changed."""
        self._cache = None
        self._cache_path = None

    def refresh(self) -> List[str]:
        """Force refresh and return folder names."""
        return self.get_folder_names(use_cache=False)
