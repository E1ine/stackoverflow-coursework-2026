-- ============================================================
-- Запрос 3: Пользователи
-- Сохранить как: data/raw/users.csv
-- ============================================================
-- Только авторы вопросов из нашей выборки
-- ============================================================

SELECT TOP 50000
    u.Id,
    u.DisplayName,
    u.Reputation,
    u.CreationDate,
    u.Location,
    u.UpVotes,
    u.DownVotes,
    u.Views,
    u.LastAccessDate
FROM Users u
WHERE u.Id IN (
    SELECT DISTINCT p.OwnerUserId
    FROM Posts p
    WHERE
        p.PostTypeId = 1
        AND p.CreationDate >= '2021-01-01'
        AND p.CreationDate <  '2026-01-01'
        AND p.OwnerUserId IS NOT NULL
)
ORDER BY u.Reputation DESC
