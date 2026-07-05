from __future__ import annotations

from html import escape
from typing import Any


STATUS_LABELS = {
    "open": "идет набор",
    "waitlist": "лист ожидания",
    "closed": "набор закрыт",
}

LEAD_STATUSES = ["new", "contacted", "enrolled", "rejected", "archived"]


def course_card(course: Any) -> str:
    return (
        f"<b>{escape(course.title)}</b>\n"
        f"Направление: {escape(course.direction)}\n"
        f"Уровень: {escape(course.level)}\n"
        f"Длительность: {escape(course.duration)}\n"
        f"Статус: {STATUS_LABELS.get(course.status, course.status)}\n\n"
        f"{escape(course.short_description)}"
    )


def lead_summary(data: dict[str, Any]) -> str:
    return (
        "<b>Проверьте заявку:</b>\n\n"
        f"Имя: {escape(str(data.get('name', '')))}\n"
        f"Контакт: {escape(str(data.get('contact', '')))}\n"
        f"Направление: {escape(str(data.get('direction', '')))}\n"
        f"Курс: {escape(str(data.get('course_title', '')))}\n"
        f"Категория/возраст: {escape(str(data.get('age_category', '')))}\n"
        f"Формат: {escape(str(data.get('format_preference', '')))}\n"
        f"Удобное время: {escape(str(data.get('time_preference', '')))}\n"
        f"Комментарий: {escape(str(data.get('comment', '')))}"
    )


def admin_lead_notification(lead_id: int, data: dict[str, Any], username: str | None, created_at: str) -> str:
    tg = f"@{username}" if username else "не указан"
    return (
        "<b>Новая заявка EduLearning</b>\n\n"
        f"ID: {lead_id}\n"
        f"Имя: {escape(str(data.get('name', '')))}\n"
        f"Telegram: {escape(tg)}\n"
        f"Контакт: {escape(str(data.get('contact', '')))}\n"
        f"Направление: {escape(str(data.get('direction', '')))}\n"
        f"Курс: {escape(str(data.get('course_title', '')))}\n"
        f"Категория/возраст: {escape(str(data.get('age_category', '')))}\n"
        f"Формат: {escape(str(data.get('format_preference', '')))}\n"
        f"Удобное время: {escape(str(data.get('time_preference', '')))}\n"
        f"Комментарий: {escape(str(data.get('comment', '')))}\n"
        f"Дата и время заявки: {escape(created_at)}\n"
        f"user_id: {escape(str(data.get('telegram_id', '')))}"
    )


def admin_question_notification(question_id: int, telegram_id: int, username: str | None, text: str) -> str:
    tg = f"@{username}" if username else "не указан"
    return (
        "<b>Новый вопрос EduLearning</b>\n\n"
        f"ID: {question_id}\n"
        f"Telegram: {escape(tg)}\n"
        f"user_id: {telegram_id}\n"
        f"Вопрос: {escape(text)}"
    )


def admin_lead_card(lead: dict[str, Any]) -> str:
    return (
        f"<b>Заявка #{lead['id']}</b> | {escape(lead['status'])}\n"
        f"Имя: {escape(lead['name'])}\n"
        f"Контакт: {escape(lead.get('contact') or '')}\n"
        f"Направление: {escape(lead['direction'])}\n"
        f"Курс: {escape(lead.get('course_title') or '')}\n"
        f"Формат: {escape(lead['format_preference'])}\n"
        f"Время: {escape(lead['time_preference'])}\n"
        f"Комментарий: {escape(lead.get('comment') or '')}\n"
        f"Создана: {escape(lead['created_at'])}\n"
        f"user_id: {lead['telegram_id']}"
    )
