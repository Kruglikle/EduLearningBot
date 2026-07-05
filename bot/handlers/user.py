from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import BASE_DIR, Settings
from bot.database import Database
from bot.keyboards.common import (
    back_main,
    cancel_keyboard,
    confirm_keyboard,
    courses_overview_actions,
    courses_keyboard,
    direction_keyboard,
    edureading_keyboard,
    main_menu,
    options_keyboard,
)
from bot.services.courses import CourseService
from bot.services.messages import (
    admin_lead_notification,
    admin_question_notification,
    course_card,
    lead_summary,
)
from bot.states import LeadForm, QuestionForm


router = Router()

EDUREADING_IMAGE = BASE_DIR / "bot" / "data" / "edu-reading.jpg"
EDUREADING_TEXT = (
    "Книжный клуб EduReading\n\n"
    "Добро пожаловать в EduReading — книжный клуб на базе сообщества EduLearning!\n\n"
    "Это пространство для тех, кто любит книги, хочет читать регулярно и обсуждать прочитанное в приятной компании.\n\n"
    "Здесь мы вместе будем:\n"
    "• выбирать интересные книги;\n"
    "• читать их в комфортном темпе;\n"
    "• делиться впечатлениями, мыслями и любимыми цитатами;\n"
    "• обсуждать идеи, персонажей и темы, которые нас зацепили.\n\n"
    "Неважно, сколько книг вы читаете в год — одну или пятьдесят. Главное — интерес к чтению и желание открывать для себя что-то новое.\n\n"
    "Надеемся, что наш книжный клуб станет местом, куда захочется возвращаться за вдохновением, новыми знаниями и приятным общением.\n\n"
    "Приятного чтения и добро пожаловать в EduReading!"
)

AGE_OPTIONS = ["школьник", "студент", "взрослый"]
FORMAT_OPTIONS = ["индивидуально", "мини-группа", "пока не знаю"]
TIME_OPTIONS = ["будни утром", "будни днем", "будни вечером", "выходные", "другое"]


@router.message(CommandStart())
async def start(message: Message, db: Database) -> None:
    user = message.from_user
    if user:
        await db.upsert_user(user.id, user.username, user.full_name)
    await message.answer(
        "Привет! Я EduKotik, помощник EduLearning. Помогу выбрать курс и записаться на занятие 🐾",
        reply_markup=main_menu(),
    )


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Сценарий отменен. Можно начать заново из главного меню.", reply_markup=main_menu())


@router.message(Command("id"))
async def id_command(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else "неизвестно"
    await message.answer(
        f"user_id: <code>{user_id}</code>\n"
        f"chat_id: <code>{message.chat.id}</code>\n\n"
        "Для теста админки добавьте user_id в ADMIN_IDS, а chat_id в ADMIN_CHAT_ID."
    )


@router.callback_query(F.data == "flow:cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Сценарий отменен. Можно начать заново из главного меню.", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Главное меню EduLearning:", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "courses:list")
async def list_courses(callback: CallbackQuery, courses: CourseService) -> None:
    loaded = courses.load_courses()
    if not loaded:
        await callback.message.edit_text("Пока список курсов пуст. Команда EduLearning скоро его обновит.", reply_markup=back_main())
        await callback.answer()
        return
    text = "<b>Курсы EduLearning</b>\n\n" + "\n\n———\n\n".join(course_card(course) for course in loaded)
    await callback.message.edit_text(text, reply_markup=courses_overview_actions(loaded))
    await callback.answer()


@router.callback_query(F.data == "lead:start")
async def start_lead(callback: CallbackQuery, state: FSMContext, courses: CourseService) -> None:
    await state.clear()
    await state.set_state(LeadForm.direction)
    await callback.message.edit_text(
        "С какого направления начнем?",
        reply_markup=direction_keyboard(courses.directions(), include_consultation=True),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lead:direction:"), LeadForm.direction)
async def choose_direction(callback: CallbackQuery, state: FSMContext, courses: CourseService) -> None:
    direction = callback.data.split(":", 2)[2]
    if direction == "consultation":
        await state.update_data(direction="Пока не знаю, хочу консультацию", course_id="", course_title="Консультация")
        await state.set_state(LeadForm.name)
        await callback.message.edit_text("Как к вам обращаться?", reply_markup=cancel_keyboard())
        await callback.answer()
        return
    available = courses.by_direction(direction)
    await state.update_data(direction=direction)
    if not available:
        await state.update_data(course_id="", course_title="Подберем курс на консультации")
        await state.set_state(LeadForm.name)
        await callback.message.edit_text("По этому направлению сейчас нет открытых курсов. Как к вам обращаться?", reply_markup=cancel_keyboard())
    else:
        await state.set_state(LeadForm.course)
        await callback.message.edit_text("Выберите конкретный курс:", reply_markup=courses_keyboard(available, "lead:selected_course"))
    await callback.answer()


@router.callback_query(F.data.startswith("lead:course:"))
async def start_course_lead(callback: CallbackQuery, state: FSMContext, courses: CourseService) -> None:
    course_id = callback.data.split(":", 2)[2]
    course = courses.by_id(course_id)
    if not course or not course.is_available:
        await callback.answer("Курс сейчас недоступен", show_alert=True)
        return
    await state.clear()
    await state.update_data(direction=course.direction, course_id=course.id, course_title=course.title)
    await state.set_state(LeadForm.name)
    await callback.message.edit_text(f"Отлично, курс: {course.title}.\nКак к вам обращаться?", reply_markup=cancel_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("lead:selected_course:"), LeadForm.course)
async def choose_course(callback: CallbackQuery, state: FSMContext, courses: CourseService) -> None:
    course_id = callback.data.split(":", 2)[2]
    course = courses.by_id(course_id)
    if not course:
        await callback.answer("Не нашел этот курс. Попробуйте выбрать еще раз.", show_alert=True)
        return
    await state.update_data(course_id=course.id, course_title=course.title)
    await state.set_state(LeadForm.name)
    await callback.message.edit_text("Как к вам обращаться?", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(LeadForm.name)
async def collect_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Напишите имя чуть подробнее, пожалуйста.", reply_markup=cancel_keyboard())
        return
    await state.update_data(name=name)
    await state.set_state(LeadForm.age_category)
    await message.answer("Выберите категорию:", reply_markup=options_keyboard("lead:age", AGE_OPTIONS))


@router.callback_query(F.data.startswith("lead:age:"), LeadForm.age_category)
async def collect_age(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(age_category=callback.data.split(":", 2)[2])
    await state.set_state(LeadForm.contact)
    await callback.message.edit_text(
        "Оставьте контакт для связи: телефон или email. Если удобнее Telegram, можно написать свой username.",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(LeadForm.contact)
async def collect_contact(message: Message, state: FSMContext) -> None:
    contact = (message.text or "").strip()
    if len(contact) < 3:
        await message.answer("Нужен контакт для связи: телефон, email или Telegram username.", reply_markup=cancel_keyboard())
        return
    await state.update_data(contact=contact)
    await state.set_state(LeadForm.format_preference)
    await message.answer("Какой формат занятий удобнее?", reply_markup=options_keyboard("lead:format", FORMAT_OPTIONS))


@router.callback_query(F.data.startswith("lead:format:"), LeadForm.format_preference)
async def collect_format(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(format_preference=callback.data.split(":", 2)[2])
    await state.set_state(LeadForm.time_preference)
    await callback.message.edit_text("Когда удобнее заниматься?", reply_markup=options_keyboard("lead:time", TIME_OPTIONS))
    await callback.answer()


@router.callback_query(F.data.startswith("lead:time:"), LeadForm.time_preference)
async def collect_time(callback: CallbackQuery, state: FSMContext) -> None:
    time_value = callback.data.split(":", 2)[2]
    if time_value == "другое":
        await state.set_state(LeadForm.custom_time)
        await callback.message.edit_text("Напишите удобное время текстом.", reply_markup=cancel_keyboard())
    else:
        await state.update_data(time_preference=time_value)
        await state.set_state(LeadForm.comment)
        await callback.message.edit_text(
            "Напишите, какая у вас цель",
            reply_markup=cancel_keyboard(),
        )
    await callback.answer()


@router.message(LeadForm.custom_time)
async def collect_custom_time(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer("Напишите удобное время чуть подробнее.", reply_markup=cancel_keyboard())
        return
    await state.update_data(time_preference=text)
    await state.set_state(LeadForm.comment)
    await message.answer(
        "Напишите, какая у вас цель",
        reply_markup=cancel_keyboard(),
    )


@router.message(LeadForm.comment)
async def collect_comment(message: Message, state: FSMContext) -> None:
    await state.update_data(comment=(message.text or "").strip())
    data = await state.get_data()
    await state.set_state(LeadForm.confirm)
    await message.answer(lead_summary(data), reply_markup=confirm_keyboard())


@router.callback_query(F.data == "lead:restart")
async def restart_lead(callback: CallbackQuery, state: FSMContext, courses: CourseService) -> None:
    await start_lead(callback, state, courses)


@router.callback_query(F.data == "lead:submit", LeadForm.confirm)
async def submit_lead(callback: CallbackQuery, state: FSMContext, db: Database, settings: Settings, bot: Bot) -> None:
    user = callback.from_user
    if not await db.can_submit_lead(user.id):
        await callback.answer("Заявку уже приняли недавно. Команда EduLearning скоро свяжется с вами.", show_alert=True)
        return
    data = await state.get_data()
    data["telegram_id"] = user.id
    lead_id = await db.create_lead(data)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    await state.clear()
    await callback.message.edit_text(
        "Готово! EduKotik передал вашу заявку команде EduLearning 🐾 Мы свяжемся с вами и поможем выбрать подходящий формат занятий.",
        reply_markup=main_menu(),
    )
    await callback.answer()
    if settings.admin_chat_id:
        await bot.send_message(
            settings.admin_chat_id,
            admin_lead_notification(lead_id, data, user.username, created_at),
        )


@router.callback_query(F.data == "question:start")
async def start_question(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(QuestionForm.text)
    await callback.message.edit_text("Напишите ваш вопрос, и я передам его команде EduLearning.", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(QuestionForm.text)
async def collect_question(message: Message, state: FSMContext, db: Database, settings: Settings, bot: Bot) -> None:
    text = (message.text or "").strip()
    if len(text) < 5:
        await message.answer("Вопрос получился слишком коротким. Напишите чуть подробнее.", reply_markup=cancel_keyboard())
        return
    user = message.from_user
    if not user:
        return
    if not await db.can_submit_question(user.id):
        await message.answer("Вопрос уже передан недавно. Дождитесь ответа команды EduLearning.", reply_markup=main_menu())
        await state.clear()
        return
    question_id = await db.create_question(user.id, user.username, text)
    await state.clear()
    await message.answer("Спасибо! EduKotik передал вопрос команде EduLearning. Мы скоро ответим 🐾", reply_markup=main_menu())
    if settings.admin_chat_id:
        await bot.send_message(settings.admin_chat_id, admin_question_notification(question_id, user.id, user.username, text))


@router.callback_query(F.data == "info:contacts")
async def contacts(callback: CallbackQuery, settings: Settings) -> None:
    lines = [
        "<b>Контакты EduLearning</b>",
        f"Сайт: {settings.project_site}",
    ]
    if settings.contact_telegram:
        lines.append(f"Telegram: {settings.contact_telegram}")
    if settings.contact_email:
        lines.append(f"Email: {settings.contact_email}")
    lines.append("\nВы можете оставить заявку прямо здесь, и команда EduLearning свяжется с вами.")
    await callback.message.edit_text("\n".join(lines), reply_markup=back_main())
    await callback.answer()


@router.callback_query(F.data == "info:edureading")
async def edureading(callback: CallbackQuery) -> None:
    if EDUREADING_IMAGE.exists():
        await callback.message.answer_photo(
            photo=FSInputFile(EDUREADING_IMAGE),
            caption=EDUREADING_TEXT,
            reply_markup=edureading_keyboard(),
        )
        with suppress(Exception):
            await callback.message.delete()
    else:
        await callback.message.edit_text(EDUREADING_TEXT, reply_markup=edureading_keyboard())
    await callback.answer()


@router.callback_query(F.data == "info:about")
async def about(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "EduLearning — это практические курсы по английскому, 3D-дизайну, Python, AI и NLP. "
        "Мы помогаем учиться через понятные объяснения, практику и поддержку преподавателей.",
        reply_markup=back_main(),
    )
    await callback.answer()
