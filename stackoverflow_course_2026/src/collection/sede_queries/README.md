# SQL-запросы для Stack Exchange Data Explorer

## Как пользоваться

1. Открой https://data.stackexchange.com/stackoverflow/query/new
2. Вставь содержимое нужного .sql файла
3. Нажми **Run Query**
4. Нажми **Download CSV**
5. Сохрани в `data/raw/` с именем из таблицы ниже

## Порядок выполнения

| Файл | Сохранить как | Что внутри |
|------|--------------|------------|
| `01_questions.sql` | `data/raw/questions.csv` | 50к вопросов 2021–2026 |
| `02_answers.sql` | `data/raw/answers.csv` | Ответы к этим вопросам |
| `03_users.sql` | `data/raw/users.csv` | Авторы вопросов |

## После скачивания

```bash
python src/storage/loader.py --load
```
