from aiogram.fsm.state import State, StatesGroup


class LeadForm(StatesGroup):
    direction = State()
    course = State()
    name = State()
    age_category = State()
    contact = State()
    format_preference = State()
    time_preference = State()
    custom_time = State()
    comment = State()
    confirm = State()


class QuestionForm(StatesGroup):
    text = State()
