# Quitung Automn 🧾

Уеб приложение (PWA) за автоматично сканиране и обработка на български касови бележки чрез Vision Language Model (PaddleOCR-VL 1.5).

## Функционалности

- **OCR извличане** — автоматично разпознаване на дата, сума, ДДС, доставчик и номер на бележка
- **Агентна валидация** — 6 правила с confidence scoring (кръстосана проверка, формат на дата, ДДС ставка и др.)
- **Месечни отчети** — Excel с жълто маркиране на ниска увереност + PDF генериране
- **Изпращане по имейл** — автоматично изпращане на отчети до счетоводител
- **PWA** — работи офлайн, инсталира се на телефон
- **Мулти-бизнес** — поддръжка на множество фирми с покани за потребители

## Технологии

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI (Python 3.12) |
| База данни | PostgreSQL (prod) / SQLite (dev) |
| OCR модел | PaddleOCR-VL 1.5 |
| Опашка | ARQ + Redis |
| Frontend | Vanilla JS PWA (SPA с hash router) |
| Контейнери | Docker Compose (5 услуги) |
| Excel | openpyxl |
| PDF | reportlab |
| Имейл | aiosmtplib |

## Бърз старт (локално)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Приложението е достъпно на `http://localhost:8000`. В dev режим се използва MockExtractor (без нужда от GPU).

## Docker

```bash
cp .env.example .env
# Редактирай .env с твоите стойности
docker compose up --build
```

Услуги: PostgreSQL, Redis, Backend (FastAPI), Worker (ARQ), Frontend (Nginx)

## Структура

```
quitung_automn/
├── backend/
│   ├── app/
│   │   ├── auth/          # JWT автентикация, bcrypt
│   │   ├── business/      # Управление на фирми
│   │   ├── extraction/    # VLM извличане + валидация
│   │   ├── receipts/      # CRUD за бележки
│   │   ├── reports/       # Excel/PDF генериране, имейл
│   │   ├── config.py      # Pydantic Settings
│   │   ├── database.py    # SQLAlchemy
│   │   ├── models.py      # ORM модели
│   │   └── main.py        # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── css/style.css
│   ├── js/
│   │   ├── api.js         # API клиент
│   │   ├── app.js         # Инициализация
│   │   ├── router.js      # SPA hash router
│   │   └── pages/         # 8 страници (login, scan, dashboard...)
│   ├── index.html
│   ├── manifest.json
│   ├── sw.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Конфигурация

Всички настройки са чрез environment variables (виж `.env.example`):

| Променлива | Описание | По подразбиране |
|------------|----------|-----------------|
| `DATABASE_URL` | Връзка към БД | `sqlite:///./quitung.db` |
| `SECRET_KEY` | JWT секретен ключ | `dev-secret-change-in-production` |
| `VLM_ENABLED` | Използване на VLM модел | `false` |
| `REDIS_URL` | Redis за опашката | `redis://redis:6379` |
| `SMTP_HOST` | SMTP сървър за имейл | — |

## Лиценз

Частен проект — всички права запазени.
