from aiohttp import web
import pytest

from bot.web import _origin_allowed, _site_payload_to_lead


def test_site_payload_to_lead() -> None:
    lead = _site_payload_to_lead({
        "name": "Анна",
        "contact": "@anna",
        "direction": "English",
        "goal": "Хочу разговорную практику",
        "page": "https://example.com/#/contacts",
    })

    assert lead["telegram_id"] == 0
    assert lead["name"] == "Анна"
    assert lead["contact"] == "@anna"
    assert lead["direction"] == "English"
    assert "Хочу разговорную практику" in lead["comment"]


def test_site_payload_requires_contact() -> None:
    with pytest.raises(web.HTTPBadRequest):
        _site_payload_to_lead({"name": "Анна"})


def test_origin_allowed_with_configured_origin() -> None:
    class Settings:
        web_allowed_origins = {"https://kruglikle.github.io"}

    assert _origin_allowed("https://kruglikle.github.io", Settings())
    assert not _origin_allowed("https://example.com", Settings())
