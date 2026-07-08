from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot
from aiohttp import web

from bot.config import Settings
from bot.database import Database
from bot.keyboards.common import lead_status_keyboard
from bot.services.messages import admin_lead_notification


logger = logging.getLogger(__name__)


def create_app(db: Database, settings: Settings, bot: Bot) -> web.Application:
    app = web.Application(middlewares=[cors_middleware(settings)])
    app["db"] = db
    app["settings"] = settings
    app["bot"] = bot
    app.router.add_get("/health", health)
    app.router.add_options("/api/leads", options)
    app.router.add_post("/api/leads", create_site_lead)
    return app


@web.middleware
async def cors_middleware(request: web.Request, handler: Any) -> web.StreamResponse:
    settings: Settings = request.app["settings"]
    origin = request.headers.get("Origin", "").rstrip("/")
    response = await handler(request)

    if _origin_allowed(origin, settings):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"

    return response


async def health(_: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def options(_: web.Request) -> web.Response:
    return web.Response(status=204)


async def create_site_lead(request: web.Request) -> web.Response:
    settings: Settings = request.app["settings"]
    if not _origin_allowed(request.headers.get("Origin", "").rstrip("/"), settings):
        raise web.HTTPForbidden(text="Origin is not allowed")

    try:
        payload = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="Invalid JSON") from exc

    if not isinstance(payload, dict):
        raise web.HTTPBadRequest(text="Expected JSON object")

    if str(payload.get("website", "")).strip():
        return web.json_response({"ok": True})

    lead = _site_payload_to_lead(payload)
    lead_id = await request.app["db"].create_lead(lead)

    if settings.admin_chat_id:
        try:
            await request.app["bot"].send_message(
                settings.admin_chat_id,
                admin_lead_notification(lead_id, lead, None, "только что"),
                reply_markup=lead_status_keyboard(lead_id),
            )
        except Exception:
            logger.exception("Failed to notify admin about site lead %s", lead_id)

    return web.json_response({"ok": True, "lead_id": lead_id})


def _site_payload_to_lead(payload: dict[str, Any]) -> dict[str, Any]:
    name = _clean(payload.get("name"))
    contact = _clean(payload.get("contact"))
    direction = _clean(payload.get("direction")) or "Сайт"
    goal = _clean(payload.get("goal"))
    page = _clean(payload.get("page"))

    if not name:
        raise web.HTTPBadRequest(text="Name is required")
    if not contact:
        raise web.HTTPBadRequest(text="Contact is required")

    comment_parts = []
    if goal:
        comment_parts.append(f"Цель: {goal}")
    if page:
        comment_parts.append(f"Страница: {page}")
    comment = "\n".join(comment_parts) or "Заявка с сайта"

    return {
        "telegram_id": 0,
        "name": name,
        "contact": contact,
        "direction": direction,
        "course_id": "",
        "course_title": "",
        "age_category": "Не указано",
        "format_preference": "Не указано",
        "time_preference": "Не указано",
        "comment": comment,
    }


def _clean(value: Any, max_length: int = 1000) -> str:
    if value is None:
        return ""
    return str(value).strip()[:max_length]


def _origin_allowed(origin: str, settings: Settings) -> bool:
    if not origin:
        return True
    if not settings.web_allowed_origins:
        return True
    return origin in settings.web_allowed_origins
