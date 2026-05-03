# 💻 Руководство для разработчика

## Стек технологий
- **Python 3.11+**
- **PostgreSQL** (локально)
- **pandas, numpy, scikit-learn, matplotlib, seaborn, plotly**
- **SQLAlchemy, psycopg2-binary**

---

## Быстрый старт

```bash
# 1. Клонировать репо
git clone https://github.com/E1ine/stackoverflow-coursework-2026
cd stackoverflow-coursework-2026

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать .env файл
cp .env.example .env
# Вставить DATABASE_URL от локального PostgreSQL или попросить у основного разработчика

# 4. Создать схему БД (если БД пустая)
python src/storage/loader.py --init

# 5. Загрузить данные (если БД пустая)
python src/storage/loader.py --load

# 6. Проверить данные
python src/processing/clean.py
```

---

## Структура проекта

```
src/
├── sede_queries/          # SQL запросы для скачивания данных с SEDE
├── storage/
│   ├── schema.sql         # Схема БД
│   └── loader.py          # Загрузка CSV → PostgreSQL
├── processing/
│   └── clean.py           # Проверка данных после загрузки
└── analytics/             # Скрипты анализа
    ├── task1_trends.py
    ├── task2_clustering.py
    ├── task3_accepted_prediction.py
    ├── task4_response_time.py
    └── task5_procrastination.py

notebooks/                 # Сохранённые графики PNG
data/
├── raw/                   # CSV файлы из SEDE (не в git)
└── processed/             # Промежуточные данные (не в git)
```

---

## Запуск аналитики

```bash
# Запустить все задачи
python src/analytics/task1_trends.py
python src/analytics/task2_clustering.py
python src/analytics/task3_accepted_prediction.py
python src/analytics/task4_response_time.py
python src/analytics/task5_procrastination.py
```

Графики сохраняются автоматически в `notebooks/` как PNG.

---

## Схема базы данных

```
users
├── user_id (PK)
├── display_name
├── reputation
├── created_at
├── location
├── up_votes
├── down_votes
├── views
└── last_access_at

questions
├── question_id (PK)
├── title
├── body
├── tags_raw
├── created_at
├── score
├── view_count
├── answer_count
├── favorite_count
├── accepted_answer_id
├── owner_user_id
├── closed_at
└── last_activity_at

answers
├── answer_id (PK)
├── question_id
├── created_at
├── score
├── owner_user_id
└── is_accepted

tags
├── tag_id (PK)
└── tag_name

question_tags
├── question_id
└── tag_id
```

---

## Как докачать данные

1. Открой https://data.stackexchange.com/stackoverflow/query/new
2. Используй SQL запросы из `src/sede_queries/`
3. Скачай CSV и положи в `data/raw/`
4. Запусти загрузку:

```bash
python src/storage/loader.py --load-questions
python src/storage/loader.py --load-tags
```

Дубликаты удаляются автоматически через `ON CONFLICT DO NOTHING`.

---
## Скачаешь дамп данных из бд с яндекс диска 

https://disk.yandex.ru/d/9yDL_agAox5DPg
---

## Подключение к БД

Формат `.env`:
```
DATABASE_URL=postgresql://postgres:пароль@localhost:5432/stackoverflow
```

Для проверки подключения:
```bash
python src/processing/clean.py
```

---

## Ветки

| Ветка | Назначение |
|-------|-----------|
| `main` | Стабильная версия |
| `data-collection` | Сбор данных |
| `task1-trends` | Задача 1 |
| `task2-clustering` | Задача 2 |
| `task3-prediction` | Задача 3 |
| `task4-response-time` | Задача 4 |
| `task5-procrastination` | Задача 5 |
