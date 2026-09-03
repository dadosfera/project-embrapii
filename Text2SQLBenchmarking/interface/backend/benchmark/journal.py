"""Journal SQLite curto, thread-safe e baseado em snapshots imutáveis."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import threading

from .models import BenchmarkErrorCode, BenchmarkJobSnapshot


class BenchmarkJournalError(Exception):
    def __init__(self, code: BenchmarkErrorCode, public_message: str, internal_detail: str) -> None:
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.internal_detail = internal_detail


class BenchmarkJournal:
    """Persiste snapshots sem reter o lock durante trabalho pesado."""

    def __init__(self, database_path: Path) -> None:
        self._path = database_path.absolute()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS benchmark_jobs (job_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=1, check_same_thread=False)

    def create(self, snapshot: BenchmarkJobSnapshot) -> None:
        payload = json.dumps(snapshot.as_dict(), sort_keys=True, separators=(",", ":"))
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO benchmark_jobs(job_id, payload, updated_at) VALUES (?, ?, ?)",
                (snapshot.job_id, payload, snapshot.updated_at),
            )

    def save(self, snapshot: BenchmarkJobSnapshot) -> None:
        payload = json.dumps(snapshot.as_dict(), sort_keys=True, separators=(",", ":"))
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "UPDATE benchmark_jobs SET payload = ?, updated_at = ? WHERE job_id = ?",
                (payload, snapshot.updated_at, snapshot.job_id),
            )
            if cursor.rowcount != 1:
                raise BenchmarkJournalError(
                    BenchmarkErrorCode.JOB_NOT_FOUND,
                    "O job solicitado não existe.",
                    "save sem job correspondente",
                )

    def get(self, job_id: str) -> BenchmarkJobSnapshot:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM benchmark_jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if row is None:
            raise BenchmarkJournalError(
                BenchmarkErrorCode.JOB_NOT_FOUND,
                "O job solicitado não existe.",
                "job_id desconhecido",
            )
        return BenchmarkJobSnapshot.from_dict(json.loads(row[0]))

    def latest(self) -> BenchmarkJobSnapshot | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM benchmark_jobs ORDER BY updated_at DESC, rowid DESC LIMIT 1"
            ).fetchone()
        return BenchmarkJobSnapshot.from_dict(json.loads(row[0])) if row else None

    def active(self) -> BenchmarkJobSnapshot | None:
        """Retorna o job não terminal mais recente, sem depender do navegador."""

        active = self.nonterminal()
        return active[-1] if active else None

    def nonterminal(self) -> tuple[BenchmarkJobSnapshot, ...]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM benchmark_jobs ORDER BY updated_at ASC, rowid ASC"
            ).fetchall()
        return tuple(
            snapshot
            for row in rows
            if not (snapshot := BenchmarkJobSnapshot.from_dict(json.loads(row[0]))).is_terminal
        )
