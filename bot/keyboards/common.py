from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.messages import LEAD_STATUSES


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Записаться на занятие", callback_data="lead:start")],
        [InlineKeyboardButton(text="Посмотреть курсы", callback_data="courses:list")],
        [InlineKeyboardButton(text="Задать вопрос", callback_data="question:start")],
        [
            InlineKeyboardButton(text="Контакты", callback_data="info:contacts"),
            InlineKeyboardButton(text="О проекте", callback_data="info:about"),
        ],
    ])


def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data="menu:main")]])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отменить", callback_data="flow:cancel")]])


def direction_keyboard(directions: list[str], include_consultation: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=direction, callback_data=f"lead:direction:{direction}")] for direction in directions]
    if include_consultation:
        rows.append([InlineKeyboardButton(text="Пока не знаю, хочу консультацию", callback_data="lead:direction:consultation")])
    rows.append([InlineKeyboardButton(text="Отменить", callback_data="flow:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def courses_keyboard(courses: list[object], prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=getattr(course, "title"), callback_data=f"{prefix}:{getattr(course, 'id')}")] for course in courses]
    rows.append([InlineKeyboardButton(text="Отменить", callback_data="flow:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def course_action(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Записаться на этот курс", callback_data=f"lead:course:{course_id}")],
        [InlineKeyboardButton(text="В главное меню", callback_data="menu:main")],
    ])


def courses_overview_actions(courses: list[object]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Записаться: {getattr(course, 'title')}", callback_data=f"lead:course:{getattr(course, 'id')}")]
        for course in courses
        if getattr(course, "is_available", False)
    ]
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def options_keyboard(prefix: str, options: list[str], cancel: bool = True) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=option, callback_data=f"{prefix}:{option}")] for option in options]
    if cancel:
        rows.append([InlineKeyboardButton(text="Отменить", callback_data="flow:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить заявку", callback_data="lead:submit")],
        [InlineKeyboardButton(text="Изменить данные", callback_data="lead:restart")],
        [InlineKeyboardButton(text="Отменить", callback_data="flow:cancel")],
    ])


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Новые заявки", callback_data="admin:leads:new")],
        [InlineKeyboardButton(text="Все заявки", callback_data="admin:leads:all")],
        [InlineKeyboardButton(text="Вопросы пользователей", callback_data="admin:questions")],
        [InlineKeyboardButton(text="Экспорт заявок", callback_data="admin:export")],
        [InlineKeyboardButton(text="Статистика", callback_data="admin:stats")],
    ])


def lead_status_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=status, callback_data=f"admin:status:{lead_id}:{status}")]
        for status in LEAD_STATUSES
    ])
