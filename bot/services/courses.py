from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    direction: str
    level: str
    duration: str
    short_description: str
    status: str

    @property
    def is_available(self) -> bool:
        return self.status in {"open", "waitlist"}


class CourseService:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._cache: list[Course] | None = None
        self._mtime: float | None = None

    def load_courses(self) -> list[Course]:
        mtime = self.path.stat().st_mtime
        if self._cache is not None and self._mtime == mtime:
            return self._cache
        with self.path.open("r", encoding="utf-8") as file:
            raw_courses = json.load(file)
        self._cache = [Course(**item) for item in raw_courses]
        self._mtime = mtime
        return self._cache

    def directions(self) -> list[str]:
        seen: list[str] = []
        for course in self.load_courses():
            if course.direction not in seen:
                seen.append(course.direction)
        return seen

    def by_direction(self, direction: str) -> list[Course]:
        return [course for course in self.load_courses() if course.direction == direction and course.is_available]

    def by_id(self, course_id: str) -> Course | None:
        return next((course for course in self.load_courses() if course.id == course_id), None)
