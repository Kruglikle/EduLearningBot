import pytest

from bot.database import Database


@pytest.mark.asyncio
async def test_create_lead(tmp_path) -> None:
    db = Database(tmp_path / "test.db")
    await db.init()

    lead_id = await db.create_lead({
        "telegram_id": 123,
        "name": "Иван",
        "contact": "@ivan",
        "direction": "Python",
        "course_id": "python-start",
        "course_title": "Python",
        "age_category": "студент",
        "format_preference": "мини-группа",
        "time_preference": "будни вечером",
        "comment": "Хочу начать программировать",
    })
    leads = await db.get_recent_leads()

    assert lead_id == 1
    assert leads[0]["name"] == "Иван"
    assert leads[0]["status"] == "new"
