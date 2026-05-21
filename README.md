# StackOverflow Analysis 2026

Курсовой проект по дисциплине «Наука о данных и аналитика больших объёмов информации»  
СПбПУ Петра Великого, 2026

---

## Цель проекта

Разработка программного комплекса для автоматического сбора, хранения и анализа данных платформы Stack Overflow с применением методов машинного обучения и статистического анализа.

---

## Аналитические задачи

| # | Задача | Тип | Метод |
|---|--------|-----|-------|
| 1 | Анализ трендов популярности технологий по тегам | Статистическая | Временные ряды, агрегация |
| 2 | Кластеризация пользователей по паттернам активности | Исследовательская | K-Means, PCA |
| 3 | Предсказание, получит ли вопрос принятый ответ | Исследовательская | Random Forest, Gradient Boosting |
| 4 | Анализ времени ожидания ответа и факторов влияния | Статистическая | Корреляционный анализ |
| 5 | Анализ временных паттернов активности («прокрастинация») | Статистическая | Временное распределение, heatmap |

---

## Структура репозитория

```text
stackoverflow-coursework-2026/
│
├── data/
│   ├── raw/                    # Сырые CSV из SEDE (в git не попадают)
│   ├── processed/              # Промежуточные данные (в git не попадают)
│   └── README.md               # Описание датасета и схема полей
│
├── src/
│   ├── sede_queries/           # SQL-запросы для Stack Exchange Data Explorer
│   │   ├── 01_questions.sql
│   │   ├── 02_answers.sql
│   │   ├── 03_users.sql
│   │   └── README.md
│   │
│   ├── storage/
│   │   ├── schema.sql         # DDL-схема PostgreSQL
│   │   └── loader.py          # Загрузка CSV → PostgreSQL
│   │
│   ├── processing/
│   │   └── clean.py           # Проверка данных после загрузки
│   │
│   └── analytics/             # Скрипты анализа
│       ├── task1_trends.py
│       ├── task2_clustering.py
│       ├── task3_accepted_prediction.py
│       ├── task4_response_time.py
│       └── task5_procrastination.py
│
├── notebooks/                 # Графики PNG (результаты анализа)
│
├── docs/
│   ├── for_analysts.md        # Руководство для аналитиков
│   └── for_developer.md       # Руководство для разработчика
│
├── .env.example               # Шаблон переменных окружения
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Стек технологий

- **Язык:** Python 3.11+
- **База данных:** PostgreSQL 16 (локально)
- **Сбор данных:** Stack Exchange Data Explorer (SEDE)
- **Обработка:** pandas, numpy
- **ML / Анализ:** scikit-learn, scipy
- **Визуализация:** matplotlib, seaborn
- **Контроль версий:** Git / GitHub

---

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/E1ine/stackoverflow-coursework-2026
cd stackoverflow-coursework-2026

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать файл .env
cp .env.example .env
# Вставить DATABASE_URL своей локальной БД

# 4. Создать схему БД
python src/storage/loader.py --init

# 5. Загрузить данные (после скачивания CSV из SEDE)
python src/storage/loader.py --load

# 6. Проверить загрузку
python src/processing/clean.py

# 7. Запустить аналитику
python src/analytics/task1_trends.py
```

---

## Источник данных

Данные получены через **Stack Exchange Data Explorer (SEDE)**:  
[https://data.stackexchange.com/stackoverflow/query/new](https://data.stackexchange.com/stackoverflow/query/new)

**Период:** Июнь 2024 — Апрель 2026

| Таблица | Записей |
|---------|---------|
| questions | ~52 000 |
| answers | ~47 000 |
| users | ~50 000 |
| tags | ~15 000 |

Подробнее в [`data/README.md`](data/README.md)

---

## Документация

- [`docs/for_analysts.md`](docs/for_analysts.md) — руководство для аналитиков: где брать графики
- [`docs/for_developer.md`](docs/for_developer.md) — руководство для разработчика: быстрый старт, схема БД, как докачать данные, откуда брать дамп данных