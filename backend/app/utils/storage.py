import os
import uuid
from pathlib import Path

import structlog

from app.config import settings

logger = structlog.get_logger()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
}

# Magic bytes for file type verification
MAGIC_BYTES = {
    b"%PDF": "application/pdf",
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}


class StorageService:
    def __init__(self, upload_dir: str | None = None):
        self.upload_dir = Path(upload_dir or settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _verify_file_type(self, content: bytes, claimed_mime: str) -> bool:
        for magic, mime in MAGIC_BYTES.items():
            if content[: len(magic)] == magic:
                # PDF, PNG match directly; JPEG variants all map to image/jpeg
                if mime == claimed_mime or (
                    mime == "image/jpeg" and claimed_mime in ("image/jpeg", "image/jpg")
                ):
                    return True
        return False

    async def save_file(
        self, content: bytes, filename: str, mime_type: str, case_id: str
    ) -> str:
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"File type {mime_type} is not allowed")

        max_size = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_size:
            raise ValueError(
                f"File size exceeds maximum of {settings.max_upload_size_mb}MB"
            )

        if not self._verify_file_type(content, mime_type):
            raise ValueError("File content does not match claimed file type")

        # Create case-specific directory
        case_dir = self.upload_dir / str(case_id)
        case_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to prevent collisions
        ext = Path(filename).suffix
        safe_name = f"{uuid.uuid4().hex}{ext}"
        file_path = case_dir / safe_name

        file_path.write_bytes(content)
        logger.info("file_saved", path=str(file_path), size=len(content))
        return str(file_path)

    async def read_file(self, file_path: str) -> bytes:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        # Ensure the path is within uploads directory to prevent directory traversal
        if not path.resolve().is_relative_to(self.upload_dir.resolve()):
            raise ValueError("Invalid file path")
        return path.read_bytes()

    async def delete_file(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists() and path.resolve().is_relative_to(self.upload_dir.resolve()):
            path.unlink()
            logger.info("file_deleted", path=str(path))


storage_service = StorageService()
