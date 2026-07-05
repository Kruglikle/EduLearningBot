from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import Settings
from bot.database import Database
from bot.keyboards.common import admin_menu, lead_status_keyboard
from bot.services.messages import admin_lead_card


router = Router()


def _is_admin(settings: Settings, user_id: int | None, chat_id: int | None) -> bool:
    return settings.is_admin(user_id, chat_id)


@router.message(Command("admin"))
async def admin_command(message: Message, settings: Settings) -> None:
    if not _is_admin(settings, message.from_user.id if message.from_user else None, message.chat.id):
        await message.answer("Эта команда доступна только администратору.")
        return
    await message.answer("Админ-меню EduLearning:", reply_markup=admin_menu())


@router.message(Command("export_leads"))
async def export_leads_command(message: Message, db: Database, settings: Settings) -> None:
    if not _is_admin(settings, message.from_user.id if message.from_user else None, message.chat.id):
        await message.answer("Эта команда доступна только администратору.")
        return
    await _send_export(message, db)


@router.callback_query(F.data.startswith("admin:"))
async def admin_callbacks(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    if not _is_admin(settings, callback.from_user.id, callback.message.chat.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    data = callback.data
    if data == "admin:leads:new":
        await _send_leads(callback.message, db, status="new")
    elif data == "admin:leads:all":
        await _send_leads(callback.message, db, status=None)
    elif data == "admin:questions":
        await _send_questions(callback.message, db)
    elif data == "admin:export":
        await _send_export(callback.message, db)
    elif data == "admin:stats":
        await _send_stats(callback.message, db)
    elif data.startswith("admin:status:"):
        _, _, lead_id, status = data.split(":", 3)
        changed = await db.update_lead_status(int(lead_id), status)
        await callback.answer("Статус обновлен" if changed else "Заявка не найдена", show_alert=not changed)
        return
    await callback.answer()


async def _send_leads(message: Message, db: Database, status: str | None) -> None:
    leads = await db.get_recent_leads(limit=10, status=status)
    if not leads:
        await message.answer("Заявок пока нет.")
        return
    for lead in leads:
        await message.answer(admin_lead_card(lead), reply_markup=lead_status_keyboard(lead["id"]))


async def _send_questions(message: Message, db: Database) -> None:
    questions = await db.get_questions(limit=10)
    if not questions:
        await message.answer("Вопросов пока нет.")
        return
    for question in questions:
        username = f"@{question['username']}" if question.get("username") else "не указан"
        await message.answer(
            f"<b>Вопрос #{question['id']}</b>\n"
            f"Telegram: {username}\n"
            f"user_id: {question['telegram_id']}\n"
            f"Статус: {question['status']}\n"
            f"Создан: {question['created_at']}\n\n"
            f"{question['question_text']}"
        )


async def _send_export(message: Message, db: Database) -> None:
    path = Path("exports") / "edulearning_leads.csv"
    await db.export_leads_csv(path)
    await message.answer_document(FSInputFile(path), caption="Экспорт заявок EduLearning")


async def _send_stats(message: Message, db: Database) -> None:
    stats = await db.stats()
    directions = "\n".join(f"- {item['direction']}: {item['count']}" for item in stats["directions"]) or "- пока нет данных"
    await message.answer(
        "<b>Статистика EduLearning</b>\n\n"
        f"Всего заявок: {stats['total']}\n"
        f"Заявок сегодня: {stats['today']}\n"
        f"Заявок за неделю: {stats['week']}\n"
        f"Вопросов: {stats['questions']}\n\n"
        f"По направлениям:\n{directions}"
    )
