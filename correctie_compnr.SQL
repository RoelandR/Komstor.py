WITH RECURSIVE digits_only(id, rest, out) AS (
    SELECT rowid,
           compnr,
           ''
    FROM components

    UNION ALL

    SELECT id,
           substr(rest, 2),
           out || CASE
                     WHEN substr(rest, 1, 1) BETWEEN '0' AND '9'
                     THEN substr(rest, 1, 1)
                     ELSE ''
                  END
    FROM digits_only
    WHERE rest <> ''
)
UPDATE components
SET compnr = (
    SELECT out
    FROM digits_only d
    WHERE d.id = components.rowid AND d.rest = ''
);
select compnr, name from components