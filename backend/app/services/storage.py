import asyncio
import hashlib
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple


def compute_sha256(data: bytes) -> str:
    """
    Computes a SHA-256 digital integrity hash for file bytes.
    Used for evidence integrity verification across the inspection lifecycle.
    """
    return hashlib.sha256(data).hexdigest()


class BaseStorageService(ABC):
    @abstractmethod
    async def save_image(
        self,
        file_bytes: bytes,
        filename: str,
        inspection_id: uuid.UUID,
        content_type: str | None = None,
    ) -> Tuple[str, str]:
        """
        Saves image bytes and returns a tuple: (stored_image_url, sha256_hash).
        """
        pass

    @abstractmethod
    async def save_report(
        self,
        file_bytes: bytes,
        filename: str,
        inspection_id: uuid.UUID,
    ) -> str:
        """Saves report document bytes and returns the stored report file URL or path."""
        pass

    @abstractmethod
    async def delete_image(self, file_url: str) -> bool:
        """Deletes an image or report file from storage."""
        pass


class LocalStorageService(BaseStorageService):
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    def _sync_save(self, target_path: Path, file_bytes: bytes) -> None:
        with open(target_path, "wb") as f:
            f.write(file_bytes)

    def _sync_delete(self, full_path: Path) -> bool:
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def save_image(
        self,
        file_bytes: bytes,
        filename: str,
        inspection_id: uuid.UUID,
        content_type: str | None = None,
    ) -> Tuple[str, str]:
        insp_dir = self.base_upload_dir / "inspections" / str(inspection_id)
        insp_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(filename).suffix or ".jpg"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        target_path = insp_dir / unique_name

        sha256_hash = compute_sha256(file_bytes)
        await asyncio.to_thread(self._sync_save, target_path, file_bytes)
        return f"/uploads/inspections/{inspection_id}/{unique_name}", sha256_hash

    async def save_report(
        self,
        file_bytes: bytes,
        filename: str,
        inspection_id: uuid.UUID,
    ) -> str:
        report_dir = self.base_upload_dir / "reports" / str(inspection_id)
        report_dir.mkdir(parents=True, exist_ok=True)

        target_path = report_dir / filename
        await asyncio.to_thread(self._sync_save, target_path, file_bytes)
        return f"/uploads/reports/{inspection_id}/{filename}"

    async def delete_image(self, file_url: str) -> bool:
        try:
            rel_path = file_url.lstrip("/")
            full_path = Path(rel_path)
            return await asyncio.to_thread(self._sync_delete, full_path)
        except Exception:
            return False


# Global storage service instance (can be swapped with S3StorageService or MinIOStorageService)
storage_service: BaseStorageService = LocalStorageService(base_upload_dir="uploads")
