from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import aiosqlite


UTC = timezone.utc


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        async with self._connect() as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    full_name TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    contact TEXT,
                    direction TEXT NOT NULL,
                    course_id TEXT,
                    course_title TEXT,
                    age_category TEXT NOT NULL,
                    format_preference TEXT NOT NULL,
                    time_preference TEXT NOT NULL,
                    comment TEXT,
                    status TEXT NOT NULL DEFAULT 'new',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    username TEXT,
                    question_text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new',
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_status_created_at ON leads(status, created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_telegram_created_at ON leads(telegram_id, created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_questions_telegram_created_at ON questions(telegram_id, created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at)")
            await db.commit()

    async def upsert_user(self, telegram_id: int, username: str | None, full_name: str) -> None:
        now = _now()
        async with self._connect() as db:
            await db.execute(
                """
                INSERT INTO users (telegram_id, username, full_name, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name
                """,
                (telegram_id, username, full_name, now),
            )
            await db.commit()

    async def create_lead(self, lead: dict[str, Any]) -> int:
        now = _now()
        async with self._connect() as db:
            cursor = await db.execute(
                """
                INSERT INTO leads (
                    telegram_id, name, contact, direction, course_id, course_title,
                    age_category, format_preference, time_preference, comment,
                    status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
                """,
                (
                    lead["telegram_id"],
                    lead["name"],
                    lead.get("contact", ""),
                    lead["direction"],
                    lead.get("course_id", ""),
                    lead.get("course_title", ""),
                    lead["age_category"],
                    lead["format_preference"],
                    lead["time_preference"],
                    lead.get("comment", ""),
                    now,
                    now,
                ),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def create_question(self, telegram_id: int, username: str | None, text: str) -> int:
        async with self._connect() as db:
            cursor = await db.execute(
                """
                INSERT INTO questions (telegram_id, username, question_text, status, created_at)
                VALUES (?, ?, ?, 'new', ?)
                """,
                (telegram_id, username, text, _now()),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def get_recent_leads(self, limit: int = 10, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM leads"
        params: list[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY datetime(created_at) DESC LIMIT ?"
        params.append(limit)
        return await self._fetch_all(query, params)

    async def get_questions(self, limit: int = 10) -> list[dict[str, Any]]:
        return await self._fetch_all(
            "SELECT * FROM questions ORDER BY datetime(created_at) DESC LIMIT ?",
            [limit],
        )

    async def update_lead_status(self, lead_id: int, status: str) -> bool:
        async with self._connect() as db:
            cursor = await db.execute(
                "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
                (status, _now(), lead_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def can_submit_lead(self, telegram_id: int, minutes: int = 10) -> bool:
        return await self._can_submit("leads", telegram_id, minutes)

    async def can_submit_question(self, telegram_id: int, minutes: int = 5) -> bool:
        return await self._can_submit("questions", telegram_id, minutes)

    async def stats(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        today = now.date().isoformat()
        week_ago = (now - timedelta(days=7)).isoformat(timespec="seconds")
        async with self._connect() as db:
            total = await _scalar(db, "SELECT COUNT(*) FROM leads")
            today_count = await _scalar(db, "SELECT COUNT(*) FROM leads WHERE date(created_at) = ?", [today])
            week_count = await _scalar(db, "SELECT COUNT(*) FROM leads WHERE datetime(created_at) >= datetime(?)", [week_ago])
            questions_count = await _scalar(db, "SELECT COUNT(*) FROM questions")
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT direction, COUNT(*) AS count FROM leads GROUP BY direction ORDER BY count DESC")
            directions = [dict(row) for row in await cursor.fetchall()]
        return {
            "total": total,
            "today": today_count,
            "week": week_count,
            "directions": directions,
            "questions": questions_count,
        }

    async def export_leads_csv(self, path: Path) -> Path:
        rows = await self._fetch_all("SELECT * FROM leads ORDER BY datetime(created_at) DESC", [])
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "id", "telegram_id", "name", "contact", "direction", "course_id", "course_title",
            "age_category", "format_preference", "time_preference", "comment", "status",
            "created_at", "updated_at",
        ]
        with path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    async def _can_submit(self, table: str, telegram_id: int, minutes: int) -> bool:
        since = (datetime.now(UTC) - timedelta(minutes=minutes)).isoformat(timespec="seconds")
        async with self._connect() as db:
            count = await _scalar(
                db,
                f"SELECT COUNT(*) FROM {table} WHERE telegram_id = ? AND datetime(created_at) >= datetime(?)",
                [telegram_id, since],
            )
        return count == 0

    async def _fetch_all(self, query: str, params: list[Any]) -> list[dict[str, Any]]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            return [dict(row) for row in await cursor.fetchall()]

    def _connect(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.path, timeout=30)


async def _scalar(db: aiosqlite.Connection, query: str, params: list[Any] | None = None) -> int:
    cursor = await db.execute(query, params or [])
    row = await cursor.fetchone()
    return int(row[0])


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
