SELECT TOP 10000
    p.Id,
    p.Title,
    p.Body,
    p.Tags,
    p.CreationDate,
    p.Score,
    p.ViewCount,
    p.AnswerCount,
    p.FavoriteCount,
    p.AcceptedAnswerId,
    p.OwnerUserId,
    p.ClosedDate,
    p.LastActivityDate
FROM Posts p
WHERE
    p.PostTypeId = 1
    AND p.CreationDate >= '2025-01-01'
    AND p.CreationDate <  '2026-01-01'
    AND p.Score > -5
ORDER BY p.CreationDate DESC