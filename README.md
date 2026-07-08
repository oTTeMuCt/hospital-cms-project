# Hospital CMS

Проект Hospital Central Management System.

## Этап 0. Подготовка окружения

В этом этапе создана базовая структура проекта, Docker Compose для локального запуска и шаблоны конфигурации.

## Структура

- backend/ — backend сервис
- frontend/ — веб-интерфейс
- bot/ — Telegram-бот

## Быстрый старт

1. Скопируйте .env.example в .env и настройте значения.
2. Запустите:
   ```bash
   docker compose up --build
   ```
3. Откройте:
   - Backend: http://localhost:8000/health/
   - Frontend: http://localhost:3000
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379
   - Bot placeholder лог не доступен через HTTP, но контейнер должен оставаться запущенным.
