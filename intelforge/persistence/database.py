from __future__ import annotations

import json
import sqlite3
from pathlib import Path

class Database:
    def __init__(self, path: str = "intelforge.db") -> None:
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, stage TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS artifacts (id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL)")
        self.connection.commit()

    def create_job(self, payload: dict) -> int:
        cursor = self.connection.execute("INSERT INTO jobs(stage,status,payload) VALUES (?,?,?)", ("context", "running", json.dumps(payload, default=str)))
        self.connection.commit(); return int(cursor.lastrowid)
    def update_job(self, job_id: int, stage: str, status: str = "running") -> None:
        self.connection.execute("UPDATE jobs SET stage=?,status=? WHERE id=?", (stage, status, job_id)); self.connection.commit()
    def save(self, job_id: int, kind: str, payload: dict) -> None:
        self.connection.execute("INSERT INTO artifacts(job_id,kind,payload) VALUES (?,?,?)", (job_id, kind, json.dumps(payload, default=str))); self.connection.commit()
    def status(self, job_id: int) -> dict | None:
        row = self.connection.execute("SELECT id,stage,status,payload FROM jobs WHERE id=?", (job_id,)).fetchone()
        return {"id": row[0], "stage": row[1], "status": row[2], "payload": json.loads(row[3])} if row else None
