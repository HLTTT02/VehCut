import shutil
from pathlib import Path, PurePath
from typing import BinaryIO
from uuid import uuid4
from app.storage.service import StorageService
from app.core.exceptions import StorageError

class LocalStorageService(StorageService):
    """Filesystem adapter. It never imports FastAPI, controllers, or repositories."""

    def __init__(self, root: Path, public_base_url: str = "/storage") -> None:
        self._root = root.resolve()
        self._public_base_url = public_base_url.rstrip("/")
        for folder in ("originals", "clips", "roi", "alerts"):
            (self._root / folder).mkdir(parents=True, exist_ok=True)

    def save_original_video(self, source: BinaryIO, filename: str) -> str:
        return self._save(source, "originals", filename)

    def save_clip(self, source: BinaryIO, filename: str) -> str:
        return self._save(source, "clips", filename)

    def save_roi_clip(self, source: BinaryIO, filename: str) -> str:
        return self._save(source, "roi", filename)

    def save_alert_image(self, source: BinaryIO, filename: str) -> str:
        return self._save(source, "alerts", filename)

    def get_file(self, storage_path: str) -> Path:
        try:
            path = (self._root / self._validate_relative_path(storage_path)).resolve()
            if not path.is_file():
                raise FileNotFoundError(storage_path)
            return path
        except (OSError, ValueError) as error:
            raise StorageError("Cannot read stored file", details={"path": storage_path}) from error

    def delete_file(self, storage_path: str) -> None:
        try:
            self.get_file(storage_path).unlink()
        except OSError as error:
            raise StorageError("Cannot delete stored file", details={"path": storage_path}) from error

    def build_file_url(self, storage_path: str) -> str:
        return f"{self._public_base_url}/{self._validate_relative_path(storage_path).as_posix()}"

    def _save(self, source: BinaryIO, folder: str, filename: str) -> str:
        safe_name = PurePath(filename).name
        if not safe_name:
            raise ValueError("Filename is required")
        relative_path = Path(folder) / f"{uuid4()}_{safe_name}"
        try:
            with (self._root / relative_path).open("wb") as target:
                shutil.copyfileobj(source, target)
        except OSError as error:
            raise StorageError("Cannot save file", details={"folder": folder}) from error
        return relative_path.as_posix()

    @staticmethod
    def _validate_relative_path(storage_path: str) -> Path:
        relative_path = Path(storage_path)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("Invalid storage path")
        return relative_path
