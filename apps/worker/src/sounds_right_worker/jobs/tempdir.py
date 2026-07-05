from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from sounds_right_worker.logging import get_logger

logger = get_logger(__name__)


class JobTempDir:
    """Per-job temporary directory manager.

    Creates a unique directory under the configured temp root and removes it on
    exit unless ``keep_files`` is set. Cleanup never raises.
    """

    def __init__(self, root: str, job_id: uuid.UUID, keep_files: bool = False) -> None:
        self._path = Path(root) / str(job_id)
        self._keep_files = keep_files

    @property
    def path(self) -> Path:
        return self._path

    def file(self, name: str) -> Path:
        return self._path / name

    def __enter__(self) -> JobTempDir:
        self._path.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, *exc: object) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        if self._keep_files:
            logger.info("keeping temp files", extra={"path": str(self._path)})
            return
        shutil.rmtree(self._path, ignore_errors=True)
