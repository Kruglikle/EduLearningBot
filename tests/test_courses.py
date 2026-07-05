from pathlib import Path

from bot.services.courses import CourseService


def test_load_courses_from_json() -> None:
    service = CourseService(Path("bot/data/courses.json"))

    courses = service.load_courses()

    assert courses
    assert {course.direction for course in courses} >= {"Английский язык", "Python", "AI / NLP"}
    assert service.by_id("python-start").title == "Python"
