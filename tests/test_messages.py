from bot.services.messages import admin_lead_notification


def test_admin_lead_notification_contains_required_fields() -> None:
    text = admin_lead_notification(
        7,
        {
            "telegram_id": 123,
            "name": "Анна",
            "contact": "anna@example.com",
            "direction": "AI / NLP",
            "course_title": "AI / NLP",
            "age_category": "взрослый",
            "format_preference": "индивидуально",
            "time_preference": "выходные",
            "comment": "Нужна консультация",
        },
        "anna",
        "2026-07-05T12:00:00+00:00",
    )

    assert "Новая заявка EduLearning" in text
    assert "Имя: Анна" in text
    assert "Telegram: @anna" in text
    assert "user_id: 123" in text
