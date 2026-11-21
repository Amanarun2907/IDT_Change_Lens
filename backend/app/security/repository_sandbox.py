import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class RepositorySandbox:
    """
    Manages isolated temporary filesystem directories for repository clones and diff analysis.
    Enforces maximum size quotas and cleanup.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = Path(settings.WORKSPACE_TEMP_DIR).resolve()
        self.workspace_path = (self.base_dir / f"session_{session_id}").resolve()

    def create(self) -> Path:
        """Creates the sandbox workspace directory."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if self.workspace_path.exists():
            self.cleanup()
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        return self.workspace_path

    def get_path(self) -> Path:
        return self.workspace_path

    def check_size(self) -> int:
        """
        Returns total workspace size in MB and raises an error if it exceeds the limit.
        """
        if not self.workspace_path.exists():
            return 0
        total_bytes = 0
        for dirpath, _, filenames in os.walk(self.workspace_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_bytes += os.path.getsize(fp)

        total_mb = total_bytes / (1024 * 1024)
        if total_mb > settings.MAX_REPO_SIZE_MB:
            raise ValueError(
                f"Repository size ({total_mb:.1f} MB) exceeds maximum allowed limit of {settings.MAX_REPO_SIZE_MB} MB."
            )
        return int(total_mb)

    def cleanup(self):
        """Safely removes the sandbox workspace."""
        if self.workspace_path.exists():
            try:
                # Windows read-only file removal handler
                def on_rm_error(func, path, exc_info):
                    try:
                        os.chmod(path, 0o777)
                        func(path)
                    except Exception:
                        pass
                shutil.rmtree(self.workspace_path, onerror=on_rm_error)
                logger.info(f"Cleaned up sandbox for session {self.session_id}")
            except Exception as e:
                logger.warning(f"Failed to cleanly remove sandbox for {self.session_id}: {e}")
