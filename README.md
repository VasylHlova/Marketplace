# Marketplace API

REST та WebSocket API для маркетплейсу з керуванням товарами, замовленнями, чергою повідомлень для сповіщень та чатом у реальному часі.

## Вимоги

* Python 3.11+ (рекомендовано 3.12)
* Docker та Docker Compose
* Redis (для запуску без Docker)

## Швидкий запуск через Docker Compose

Запуск усіх сервісів (FastAPI, Celery worker, Redis):

```bash
docker compose up --build
```

API буде доступне за адресою `http://localhost:8000`. 
Документація Swagger: `http://localhost:8000/docs`.

## Запуск локально (розробка)

1. Встановіть залежності (використовуючи `uv` або `pip`):
   ```bash
   uv sync
   # або: python -m venv .venv && source .venv/bin/activate && pip install -r pyproject.toml
   ```

2. Запустіть Redis локально.

3. Запустіть Celery воркер:
   ```bash
   celery -A app.core.celery worker -l info
   ```

4. Запустіть FastAPI сервер:
   ```bash
   fastapi dev app/main.py --port 8000
   ```

## Запуск тестів та лінтера

Запуск тестів (локально):
```bash
.venv/bin/pytest
```

Запуск тестів у Docker:

* Якщо контейнери вже запущені:
  ```bash
  docker compose exec fastapi python -m pytest
  ```
* Запуск в одноразовому контейнері (без підняття всього оточення):
  ```bash
  docker compose run --rm fastapi python -m pytest
  ```

Запуск лінтера (ruff):
```bash
.venv/bin/ruff check app/
```

---

## Інструкція користувача (User Guide)

### 1. Реєстрація та авторизація
* **Реєстрація:** `POST /api/v1/users/signup` з тілом `{"email": "user@example.com", "password": "securepassword123", "role": "buyer"}` (ролі: `buyer` або `seller`).
* **Вхід:** `POST /api/v1/login` (OAuth2 Password Request Form). Повертає JWT токен.
* **Авторизація:** Всі наступні ендпоінти (окрім публічного отримання списку товарів) вимагають заголовок `Authorization: Bearer <token>`.

### 2. Товари та замовлення
* **Створення товару (тільки Seller):** `POST /api/v1/products/` з тілом `{"name": "Товар", "price": 100.0, "stock": 10}`.
* **Перегляд товарів (публічний):** `GET /api/v1/products/` з підтримкою пагінації та фільтрації: `/api/v1/products/?min_price=50&max_price=150`.
* **Створення замовлення (тільки Buyer):** `POST /api/v1/orders/` з тілом `{"items": [{"product_id": "<uuid>", "quantity": 2}]}`. Зменшує склад товару атомарно. У разі успіху надсилає фонову задачу в Celery для логування надсилання листа.
* **Скасування замовлення (тільки Buyer-власник):** `PATCH /api/v1/orders/{id}/cancel`. Дозволено лише для активних замовлень. Атомарно повертає товар на склад.
* **Статистика продажів (для будь-якого авторизованого користувача):** `GET /api/v1/sellers/{seller_id}/summary`. Повертає загальну кількість замовлень та сумарний дохід від проданих товарів цього продавця (скасовані замовлення не враховуються).

### 3. Чат у реальному часі
* **Створення кімнати чату (тільки Buyer):** `POST /api/v1/chat/` з тілом `{"seller_id": "<seller_uuid>"}`. Створює унікальну кімнату між покупцем та продавцем.
* **Підключення до чату (WebSocket):** Встановити з'єднання з `ws://localhost:8000/api/v1/chat/{room_id}?token=<jwt_token>`.
* **Надсилання повідомлення:** Надіслати рядок у форматі тексту повідомлення через WebSocket. Повідомлення зберігається в БД та розсилається іншому учаснику кімнати.
* **Історія повідомлень:** `GET /api/v1/chat/{room_id}/history` для отримання хронологічного списку повідомлень у кімнаті.
