#!/usr/bin/env python3
"""
lock.py — per-ticket lock dengan TTL, mencegah concurrent run.
Sesuai AGENTS.md §9.6 (scope isolation).

Usage:
    from lock import TicketLock
    with TicketLock(7434) as lock:
        if not lock.acquired:
            print("skip, in-flight")
            return
        run_pipeline()
"""
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

LOCKS_DIR = Path(__file__).resolve().parent.parent.parent / 'reports' / 'locks'
DEFAULT_TTL = 300  # 5 menit


def ensure_locks_dir() -> None:
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def TicketLock(ticket_id: int, ttl: int = DEFAULT_TTL) -> Iterator['LockHandle']:
    ensure_locks_dir()
    lock_path = LOCKS_DIR / f'{ticket_id}.lock'
    handle = LockHandle(lock_path, ttl)

    if not handle.acquire():
        yield handle
        return

    try:
        yield handle
    finally:
        handle.release()


class LockHandle:
    def __init__(self, path: Path, ttl: int):
        self.path = path
        self.ttl = ttl
        self.acquired = False

    def acquire(self) -> bool:
        if self.path.exists():
            try:
                age = time.time() - self.path.stat().st_mtime
                if age > self.ttl:
                    self.path.unlink(missing_ok=True)
                else:
                    return False
            except OSError:
                return False

        try:
            self.path.write_text(f'pid={os.getpid()}\ntimestamp={int(time.time())}\n', encoding='utf-8')
            self.acquired = True
            return True
        except OSError:
            return False

    def release(self) -> None:
        if self.acquired and self.path.exists():
            try:
                self.path.unlink()
            except OSError:
                pass
        self.acquired = False
