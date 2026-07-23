"""Single-instance lock to prevent multiple trackers running simultaneously."""
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TrackerLock:
    """Ensures only one tracker instance runs at a time."""

    def __init__(self, steam_id: str, lock_dir: str = "data"):
        self.lock_file = Path(lock_dir) / f"tracker_{steam_id}.lock"
        self.acquired = False

    def acquire(self):
        """Acquire the lock. Raises RuntimeError if another instance is running."""
        if self.lock_file.exists():
            # Check if the PID in the lock file is still running
            try:
                with open(self.lock_file, 'r') as f:
                    old_pid = int(f.read().strip())

                # Check if process is still running
                if self._is_process_running(old_pid):
                    raise RuntimeError(
                        f"Another tracker instance is already running (PID {old_pid}).\n"
                        f"If this is incorrect, delete: {self.lock_file}"
                    )
                else:
                    logger.info("Found stale lock file (process not running), removing it")
                    self.lock_file.unlink()
            except (ValueError, FileNotFoundError):
                # Corrupt or missing lock file, remove it
                self.lock_file.unlink(missing_ok=True)

        # Write our PID to the lock file
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_file, 'w') as f:
            f.write(str(os.getpid()))

        self.acquired = True
        logger.info("Acquired tracker lock (PID %s)", os.getpid())

    def release(self):
        """Release the lock."""
        if self.acquired and self.lock_file.exists():
            self.lock_file.unlink()
            logger.info("Released tracker lock")
            self.acquired = False

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            # On Unix, sending signal 0 checks if process exists
            # On Windows, we need to use tasklist or psutil
            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.SubprocessError):
            return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
