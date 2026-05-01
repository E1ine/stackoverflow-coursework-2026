# 📊 StackOverflow Analysis 2026

Курсовой проект по дисциплине «Наука о данных и аналитика больших объёмов информации»  
СПбПУ Петра Великого, 2026

---

## 🎯 Цель проекта

Разработка программного комплекса для автоматического сбора, хранения и анализа данных платформы Stack Overflow с применением методов машинного обучения и статистического анализа.

---

## 📋 Аналитические задачи

| # | Задача | Тип | Метод |
|---|--------|-----|-------|
| 1 | Анализ трендов популярности технологий по тегам | Статистическая | Временные ряды, агрегация |
| 2 | Кластеризация пользователей по паттернам активности | Исследовательская | K-Means, PCA |
| 3 | Прогнозирование рейтинга (Score) вопроса | Исследовательская | Random Forest, Gradient Boosting |
| 4 | Анализ времени ожидания ответа и факторов влияния | Статистическая | Корреляционный анализ, регрессия |
| 5 | Анализ временны́х паттернов активности («прокрастинация») | Статистическая | Временно́е распределение, heatmap |

---

## 🗂️ Структура репозитория

```
stackoverflow-analysis-2026/
│
├── data/
│   ├── raw/                       # Сырые CSV из SEDE (в git не попадают)
│   ├── processed/                 # Промежуточные данные (в git не попадают)
│   └── README.md                  # Описание датасета и схема полей
│
├── src/
│   ├── collection/
│   │   └── sede_queries/          # SQL-запросы для Stack Exchange Data Explorer
│   │       ├── 01_questions.sql
│   │       ├── 02_answers.sql
│   │       ├── 03_users.sql
│   │       └── README.md
│   │
│   ├── storage/
│   │   ├── schema.sql             # DDL-схема PostgreSQL
│   │   └── loader.py              # Загрузка CSV → PostgreSQL
│   │
│   ├── processing/
│   │   └── clean.py               # Проверка данных после загрузки
│   │
│   └── analytics/                 # Скрипты анализа (по одному на задачу)
│       ├── task1_trends.py
│       ├── task2_clustering.py
│       ├── task3_score_prediction.py
│       ├── task4_response_time.py
│       └── task5_procrastination.py
│
├── notebooks/                     # Jupyter notebooks с визуализацией
│   ├── 00_EDA.ipynb
│   ├── 01_trends.ipynb
│   ├── 02_clustering.ipynb
│   ├── 03_score_prediction.ipynb
│   ├── 04_response_time.ipynb
│   └── 05_procrastination.ipynb
│
├── docs/
│   └── report.md                  # Черновик итогового отчёта
│
├── .env.example                   # Шаблон переменных окружения
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠️ Стек технологий

- **Язык:** Python 3.11+
- **База данных:** PostgreSQL (Neon.tech — облачный хостинг, единая БД для команды)
- **Сбор данных:** Stack Exchange Data Explorer (SEDE)
- **Обработка:** pandas, numpy
- **ML / Анализ:** scikit-learn, scipy
- **Визуализация:** matplotlib, seaborn, plotly
- **Контроль версий:** Git / GitHub

---

## 🚀 Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/E1ine/stackoverflow-coursework-2026
cd stackoverflow-coursework-2026

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать файл .env с данными подключения к БД
cp .env.example .env
# Открой .env и вставь DATABASE_URL от Neon

# 4. Создать схему БД
python src/storage/loader.py --init

# 5. Загрузить данные (после скачивания CSV из SEDE)
python src/storage/loader.py --load

# 6. Проверить загрузку
python src/processing/clean.py

# 7. Открыть ноутбуки
jupyter lab notebooks/
```

---

## 📦 Источник данных

Данные получены через **Stack Exchange Data Explorer (SEDE)**:  
🔗 https://data.stackexchange.com/stackoverflow/query/new

Период: 2021–2026 гг.  
Подробнее в [`data/README.md`](data/README.md)

---

## 🌿 Ветки разработки

| Ветка | Назначение |
|-------|-----------|
| `main` | Стабильная версия, только через PR |
| `data-collection` | Сбор и загрузка данных |
| `task1-trends` | Задача 1: тренды технологий |
| `task2-clustering` | Задача 2: кластеризация |
| `task3-prediction` | Задача 3: прогнозирование score |
| `task4-response-time` | Задача 4: время ответа |
| `task5-procrastination` | Задача 5: временны́е паттерны |
