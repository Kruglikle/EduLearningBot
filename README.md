# EduLearning Telegram Bot

Telegram-бот для записи на занятия EduLearning. Бот показывает курсы из `bot/data/courses.json`, собирает заявки, сохраняет их в SQLite, уведомляет администратора и дает базовую админку.

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Настройка

Скопируйте `.env.example` в `.env` и заполните значения:

```env
BOT_TOKEN=123456:telegram-token
ADMIN_CHAT_ID=123456789
ADMIN_IDS=123456789,987654321
PROJECT_SITE=https://edu-learning.ru/
CONTACT_EMAIL=info@example.com
CONTACT_TELEGRAM=@edulearning
DATABASE_URL=sqlite:///edulearning_bot.db
```

`ADMIN_CHAT_ID` используется для уведомлений о новых заявках и вопросах. `ADMIN_IDS` разрешает доступ к `/admin` и `/export_leads`.

## Запуск

```bash
python -m bot.main
```

Через Docker:

```bash
docker compose up --build -d
```

## Курсы

Курсы редактируются без изменения кода в `bot/data/courses.json`.

Поля курса:

- `id`: стабильный идентификатор, например `python-start`
- `title`: название курса
- `direction`: направление
- `level`: уровень
- `duration`: длительность
- `short_description`: краткое описание
- `status`: `open`, `waitlist` или `closed`

Курсы со статусом `closed` не предлагаются в сценарии записи.

## Команды

Пользователь:

- `/start` - главное меню
- `/cancel` - отменить текущий сценарий
- `/id` - показать `user_id` и `chat_id` для настройки админ-доступа

Администратор:

- `/admin` - меню администратора
- `/export_leads` - выгрузить заявки в CSV

В админ-меню доступны новые заявки, все заявки, вопросы пользователей, экспорт и статистика. Статус заявки меняется inline-кнопками: `new`, `contacted`, `enrolled`, `rejected`, `archived`.

## Тесты

```bash
pytest
```
