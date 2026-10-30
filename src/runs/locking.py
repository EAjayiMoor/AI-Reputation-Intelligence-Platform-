"""Nonblocking process locks; the OS releases ownership when a worker exits."""
from contextlib import contextmanager
import os
from pathlib import Path

if os.name == 'nt':
    import msvcrt
else:
    import fcntl


class RunBusyError(RuntimeError):
    pass


@contextmanager
def run_lock(path: Path):
    # Keep this file after release: deleting it could let two processes lock
    # different file objects under the same name on POSIX systems.
    with path.open('a+b') as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RunBusyError('This run is already being executed or updated by another session.') from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
