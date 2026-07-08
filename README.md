# Hospital CMS

Проект Hospital Central Management System.

## Этап 0. Подготовка окружения

В этом этапе создана базовая структура проекта, Docker Compose для локального запуска и шаблоны конфигурации.

## Структура

- backend/ — backend сервис
- frontend/ — веб-интерфейс
- bot/ — Telegram-бот

## Текущий статус

- Этап 0: подготовка окружения, `docker-compose` и базовый каркас проекта — выполнено.
- Этап 1: добавлена архитектура backend и модели для ключевых доменов (accounts, hospitals, patients, appointments, lab, medrecords, files, notifications, audit) — выполнено.
- Этап 2: реализована JWT-аутентификация, регистрация и базовый набор API для управления пользователями, а также middleware для аудита — выполнено.

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и настройте значения.
2. Запустите:
   ```bash
   docker compose up --build
   ```
3. Откройте:
   - Backend health: http://localhost:8000/health/
   - Backend auth API: http://localhost:8000/api/auth/token/
   - Frontend: http://localhost:3000
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379
   - Bot placeholder лог не доступен через HTTP, но контейнер должен оставаться запущенным.

## Тестирование backend

1. Активируйте виртуальное окружение или используйте `.\.venv\Scripts\python.exe`.
2. Запустите проверки Django:
   ```bash
   .\.venv\Scripts\python.exe backend\manage.py check
   ```
3. Запустите тесты для accounts:
   ```bash
   .\.venv\Scripts\python.exe backend\manage.py test accounts
   ```

## API endpoints

- `POST /api/auth/token/` — получить access/refresh токены
- `POST /api/auth/token/refresh/` — обновить access токен
- `POST /api/auth/register/` — регистрация пользователя
- `GET /api/auth/me/` — информация о текущем пользователе
- `GET /api/users/` — список пользователей (только для админа)
- `GET /api/users/{id}/` — детальная информация о пользователе (только для админа)
