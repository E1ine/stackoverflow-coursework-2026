# 📦 Описание датасета

## Источник

**Stack Exchange Data Explorer (SEDE)**  
🔗 https://data.stackexchange.com/stackoverflow/query/new

SEDE — официальный инструмент Stack Exchange для SQL-запросов к публичной базе Stack Overflow.  
Данные обновляются еженедельно, без ограничений API, до 50 000 строк за запрос.

---

## Как скачать данные

1. Открой SEDE по ссылке выше
2. Выполни запросы из `src/collection/sede_queries/` по порядку
3. Каждый запрос — кнопка **Download CSV**
4. Сохрани файлы в `data/raw/` с именами указанными ниже

```
data/raw/
├── questions.csv
├── answers.csv
└── users.csv
```

5. Запусти загрузку в БД:
```bash
python src/storage/loader.py --load
```

---

## Схема таблиц

### questions

| Поле | Тип | Описание |
|------|-----|----------|
| Id | int | ID вопроса |
| Title | str | Заголовок |
| Body | str | Текст вопроса |
| Tags | str | Теги: `<python><pandas>` |
| CreationDate | datetime | Дата создания |
| Score | int | Рейтинг |
| ViewCount | int | Просмотры |
| AnswerCount | int | Количество ответов |
| FavoriteCount | int | В избранном |
| AcceptedAnswerId | int | ID принятого ответа |
| OwnerUserId | int | ID автора |
| ClosedDate | datetime | Дата закрытия |

### answers

| Поле | Тип | Описание |
|------|-----|----------|
| Id | int | ID ответа |
| ParentId | int | ID вопроса |
| CreationDate | datetime | Дата ответа |
| Score | int | Рейтинг ответа |
| OwnerUserId | int | ID автора |
| IsAccepted | int | 1 если принят |

### users

| Поле | Тип | Описание |
|------|-----|----------|
| Id | int | ID пользователя |
| DisplayName | str | Имя |
| Reputation | int | Репутация |
| CreationDate | datetime | Дата регистрации |
| Location | str | Местоположение |
| UpVotes | int | Апвоты |
| DownVotes | int | Даунвоты |
| Views | int | Просмотры профиля |
