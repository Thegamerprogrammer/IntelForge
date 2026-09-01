from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

class Database:
    def __init__(self, path: str = "intelforge.db") -> None:
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, stage TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS artifacts (id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS stage_states (job_id INTEGER NOT NULL, stage_id TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(job_id, stage_id))")
        self.connection.execute("CREATE TABLE IF NOT EXISTS provider_calls (id INTEGER PRIMARY KEY, job_id INTEGER, provider TEXT NOT NULL, model TEXT, purpose TEXT NOT NULL, latency_ms INTEGER, success INTEGER NOT NULL, error TEXT, created_at TEXT NOT NULL)")
        # Forward-compatible migration for databases created by the skeleton release.
        for table in ("jobs", "artifacts"):
            columns = {row[1] for row in self.connection.execute(f"PRAGMA table_info({table})")}
            if "created_at" not in columns:
                self.connection.execute(f"ALTER TABLE {table} ADD COLUMN created_at TEXT")
        self.connection.commit()

    def create_job(self, payload: dict) -> int:
        cursor = self.connection.execute("INSERT INTO jobs(stage,status,payload,created_at) VALUES (?,?,?,?)", ("context", "running", json.dumps(payload, default=str), datetime.now(timezone.utc).isoformat()))
        self.connection.commit(); return int(cursor.lastrowid)
    def update_job(self, job_id: int, stage: str, status: str = "running") -> None:
        self.connection.execute("UPDATE jobs SET stage=?,status=? WHERE id=?", (stage, status, job_id)); self.connection.commit()
    def save(self, job_id: int, kind: str, payload: object) -> int:
        cursor = self.connection.execute("INSERT INTO artifacts(job_id,kind,payload,created_at) VALUES (?,?,?,?)", (job_id, kind, json.dumps(payload, default=str), datetime.now(timezone.utc).isoformat())); self.connection.commit(); return int(cursor.lastrowid)
    def artifacts(self, job_id: int, kind: str | None = None) -> list[dict]:
        sql, params = "SELECT id,kind,payload,created_at FROM artifacts WHERE job_id=?", [job_id]
        if kind: sql += " AND kind=?"; params.append(kind)
        return [{"id": row[0], "kind": row[1], "payload": json.loads(row[2]), "created_at": row[3]} for row in self.connection.execute(sql, params).fetchall()]
    def latest(self, job_id: int, kind: str) -> object | None:
        rows = self.artifacts(job_id, kind)
        return rows[-1]["payload"] if rows else None
    def save_stage(self, job_id: int, stage_id: str, payload: dict) -> None:
        self.connection.execute("INSERT OR REPLACE INTO stage_states(job_id,stage_id,payload) VALUES (?,?,?)", (job_id, stage_id, json.dumps(payload))); self.connection.commit()
    def stages(self, job_id: int) -> list[dict]:
        return [{"stage_id": r[0], **json.loads(r[1])} for r in self.connection.execute("SELECT stage_id,payload FROM stage_states WHERE job_id=?", (job_id,)).fetchall()]
    def record_provider_call(self, job_id: int | None, provider: str, purpose: str, *, model: str | None = None, latency_ms: int | None = None, success: bool = True, error: str | None = None) -> None:
        self.connection.execute("INSERT INTO provider_calls(job_id,provider,model,purpose,latency_ms,success,error,created_at) VALUES (?,?,?,?,?,?,?,?)", (job_id, provider, model, purpose, latency_ms, int(success), error, datetime.now(timezone.utc).isoformat())); self.connection.commit()
    def status(self, job_id: int) -> dict | None:
        row = self.connection.execute("SELECT id,stage,status,payload,created_at FROM jobs WHERE id=?", (job_id,)).fetchone()
        return {"id": row[0], "stage": row[1], "status": row[2], "payload": json.loads(row[3]), "created_at": row[4], "stages": self.stages(job_id)} if row else None
