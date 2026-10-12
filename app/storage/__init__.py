"""Storage abstractions and adapters."""

from app.storage.local_storage import LocalStorageService
from app.storage.service import StorageService

__all__ = ["LocalStorageService", "StorageService"]
