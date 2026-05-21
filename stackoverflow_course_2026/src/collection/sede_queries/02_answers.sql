-- ============================================================
-- Запрос 2: Ответы
-- Сохранить как: data/raw/answers.csv
-- ============================================================
-- Нужен для задачи 4 (время ожидания ответа)
-- ============================================================

SELECT TOP 50000
    a.Id,
    a.ParentId,
    a.CreationDate,
    a.Score,
    a.OwnerUserId,
    CASE WHEN q.AcceptedAnswerId = a.Id THEN 1 ELSE 0 END AS IsAccepted
FROM Posts a
JOIN Posts q ON q.Id = a.ParentId
WHERE
    a.PostTypeId = 2
    AND q.PostTypeId = 1
    AND q.CreationDate >= '2021-01-01'
    AND q.CreationDate <  '2026-01-01'
ORDER BY a.ParentId, a.CreationDate ASC
