-- Index query 2 seperate queries
-- Index query for invoice
SELECT
    h.id,
    'INV-' || h.bill_num AS bill_num,
    h.bill_timestamp,
    COALESCE(b1.name, '') AS billed_to,
    COALESCE(b2.name, '') AS shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount,
    '[' || GROUP_CONCAT (
        '{"descp":"' || g.descp || '","hsn_sac":"' || g.hsn_sac || '","uom":"' || g.uom || '","rate":' || g.rate || ',"gst":' || g.gst || ',"qty":' || hg.qty || '}',
        ','
    ) || ']' AS list_of_goods
FROM
    history AS h
    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
    LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
    LEFT JOIN history_goods AS hg ON h.id = hg.history_id
    LEFT JOIN goods AS g ON hg.goods_id = g.id
WHERE
    h.company_id = ?
    AND h.type = 'Invoice'
GROUP BY
    h.id,
    h.bill_num,
    h.bill_timestamp,
    billed_to,
    shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount
ORDER BY
    h.id DESC
LIMIT
    5;

-- Index query for quotation
SELECT
    h.id,
    'EST-' || h.bill_num AS bill_num,
    h.bill_timestamp,
    COALESCE(b1.name, '') AS billed_to,
    h.eta,
    h.amount,
    '[' || GROUP_CONCAT (
        '{"descp":"' || g.descp || '","hsn_sac":"' || g.hsn_sac || '","uom":"' || g.uom || '","rate":' || g.rate || ',"gst":' || g.gst || ',"qty":' || hg.qty || '}',
        ','
    ) || ']' AS list_of_goods
FROM
    history AS h
    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
    LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
    LEFT JOIN history_goods AS hg ON h.id = hg.history_id
    LEFT JOIN goods AS g ON hg.goods_id = g.id
WHERE
    h.company_id = ?
    AND h.type = 'Quotation'
GROUP BY
    h.id,
    h.bill_num,
    h.bill_timestamp,
    billed_to,
    h.eta,
    h.amount
ORDER BY
    h.id DESC
LIMIT
    5;

-- Index query for invoice json function
SELECT
    h.id,
    CASE
        WHEN h.type = 'Invoice' THEN 'INV-' || h.bill_num
        ELSE 'EST-' || h.bill_num
    END AS bill_num,
    h.bill_timestamp,
    COALESCE(b1.name, '') AS billed_to,
    COALESCE(b2.name, '') AS shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount,
    json_group_array (
        json_object (
            'descp',
            g.descp,
            'hsn_sac',
            g.hsn_sac,
            'uom',
            g.uom,
            'rate',
            g.rate,
            'gst',
            g.gst,
            'qty',
            hg.qty
        )
    ) AS list_of_goods
FROM
    history AS h
    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
    LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
    LEFT JOIN history_goods AS hg ON h.id = hg.history_id
    LEFT JOIN goods AS g ON hg.goods_id = g.id
WHERE
    h.company_id = ?
    AND h.type = ?
GROUP BY
    h.id,
    h.bill_num,
    h.bill_timestamp,
    billed_to,
    shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount
ORDER BY
    h.id DESC
LIMIT
    5;

-- History query
SELECT
    h.id,
    CASE
        WHEN h.type = 'Invoice' THEN 'INV-' || h.bill_num
        ELSE 'EST-' || h.bill_num
    END AS bill_num,
    h.bill_timestamp,
    h.type,
    COALESCE(b1.name, '') AS billed_to,
    COALESCE(b2.name, '') AS shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount,
    '[' || GROUP_CONCAT (
        '{"descp":"' || g.descp || '","hsn_sac":"' || g.hsn_sac || '","uom":"' || g.uom || '","rate":' || g.rate || ',"gst":' || g.gst || ',"qty":' || hg.qty || '}',
        ','
    ) || ']' AS list_of_goods
FROM
    history AS h
    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
    LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
    LEFT JOIN history_goods AS hg ON h.id = hg.history_id
    LEFT JOIN goods AS g ON hg.goods_id = g.id
WHERE
    h.company_id = ?
GROUP BY
    h.id,
    h.bill_num,
    h.bill_timestamp,
    h.type,
    billed_to,
    shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount
ORDER BY
    h.id DESC;

-- History query json function
SELECT
    h.id,
    CASE
        WHEN h.type = 'Invoice' THEN 'INV-' || h.bill_num
        ELSE 'EST-' || h.bill_num
    END AS bill_num,
    h.bill_timestamp,
    h.type,
    COALESCE(b1.name, '') AS billed_to,
    COALESCE(b2.name, '') AS shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount,
    json_group_array (
        json_object (
            'descp',
            g.descp,
            'hsn_sac',
            g.hsn_sac,
            'uom',
            g.uom,
            'rate',
            g.rate,
            'gst',
            g.gst,
            'qty',
            hg.qty
        )
    ) AS list_of_goods
FROM
    history AS h
    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
    LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
    LEFT JOIN history_goods AS hg ON h.id = hg.history_id
    LEFT JOIN goods AS g ON hg.goods_id = g.id
WHERE
    h.company_id = ?
GROUP BY
    h.id,
    h.bill_num,
    h.bill_timestamp,
    h.type,
    billed_to,
    shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount
ORDER BY
    h.id DESC;

-- Rough Inventory query broken
SELECT
    json_group_array (
        json_object (
            'descp',
            g.descp,
            'hsn_sac',
            g.hsn_sac,
            'uom',
            g.uom,
            'rate',
            g.rate,
            'gst',
            g.gst,
            'added_at',
            g.added_at,
            'added_by',
            u1.username
        )
    ) AS goods,
    json_group_array (
        json_object (
            'name',
            b.name,
            'addr',
            COALESCE(
                b.addrBnm || ' ' || b.addrBno || ' ' || b.addrFlno || ' ' || b.addrSt || ' ' || b.addrLoc || ' ' || b.addrDist || '-' || b.addrPncd || ' ' || b.addrState,
                ''
            ),
            'phno',
            COALESCE(b.phno1 || ', ' || b.phno2, ''),
            'gstin',
            b.gstin,
            'added_at',
            b.added_at,
            'added_by',
            u2.username
        )
    ) AS clients
FROM
    companies AS c
    LEFT JOIN goods AS g ON c.id = g.company_id
    LEFT JOIN beneficiaries AS b ON c.id = b.company_id
    LEFT JOIN users as u1 on g.added_by = u1.id
    LEFT JOIN users AS u2 ON b.added_by = u2.id
WHERE
    c.id = ?;

-- Rough Inventory query broken
SELECT
    json_group_array (
        json_object (
            'descp',
            g.descp,
            'hsn_sac',
            g.hsn_sac,
            'uom',
            g.uom,
            'rate',
            g.rate,
            'gst',
            g.gst,
            'added_at',
            g.added_at,
            'added_by',
            u1.username
        )
    ) AS goods
FROM
    companies AS c
    LEFT JOIN goods AS g ON c.id = g.company_id
    LEFT JOIN users as u1 on g.added_by = u1.id
WHERE
    c.id = ?;

-- Inventory query
WITH
    goods_data AS (
        SELECT
            g.descp,
            g.hsn_sac,
            g.uom,
            g.rate,
            g.gst,
            g.added_at,
            u1.username
        FROM
            goods AS g
            JOIN users AS u1 ON g.added_by = u1.id
        WHERE
            g.company_id = c.id
    ),
    clients_data AS (
        SELECT
            b.name,
            COALESCE(
                b.addrBnm || ' ' || b.addrBno || ' ' || b.addrFlno || ' ' || b.addrSt || ' ' || b.addrLoc || ' ' || b.addrDist || '-' || b.addrPncd || ' ' || b.addrState,
                ''
            ) AS addr,
            COALESCE(b.phno1 || ', ' || b.phno2, '') AS phno,
            b.gstin,
            b.added_at,
            u2.username
        FROM
            beneficiaries AS b
            JOIN users AS u2 ON b.added_by = u2.id
        WHERE
            b.company_id = c.id
    )
SELECT
    (
        SELECT
            json_group_array (
                json_object (
                    'descp',
                    descp,
                    'hsn_sac',
                    hsn_sac,
                    'uom',
                    uom,
                    'rate',
                    rate,
                    'gst',
                    gst,
                    'added_at',
                    added_at,
                    'added_by',
                    username
                )
            )
        FROM
            goods_data
    ) AS goods,
    (
        SELECT
            json_group_array (
                json_object (
                    'name',
                    name,
                    'addr',
                    addr,
                    'phno',
                    phno,
                    'gstin',
                    gstin,
                    'added_at',
                    added_at,
                    'added_by',
                    username
                )
            )
        FROM
            clients_data
    ) AS clients
FROM
    companies AS c
WHERE
    c.id = ?;

-- Alt. Inventory query
WITH
    goods_data AS (
        SELECT
            json_group_array (
                json_object (
                    'descp',
                    g.descp,
                    'hsn_sac',
                    g.hsn_sac,
                    'uom',
                    g.uom,
                    'rate',
                    g.rate,
                    'gst',
                    g.gst,
                    'added_at',
                    g.added_at,
                    'added_by',
                    u1.username
                )
            ) AS goods
        FROM
            goods AS g
            JOIN users AS u1 ON g.added_by = u1.id
        WHERE
            g.company_id = c.id
    ),
    clients_data AS (
        SELECT
            json_group_array (
                json_object (
                    'name',
                    b.name,
                    'addr',
                    COALESCE(
                        b.addrBnm || ' ' || b.addrBno || ' ' || b.addrFlno || ' ' || b.addrSt || ' ' || b.addrLoc || ' ' || b.addrDist || '-' || b.addrPncd || ' ' || b.addrState,
                        ''
                    ),
                    'phno',
                    COALESCE(b.phno1 || ', ' || b.phno2, ''),
                    'gstin',
                    b.gstin,
                    'added_at',
                    b.added_at,
                    'added_by',
                    u2.username
                )
            ) AS clients
        FROM
            beneficiaries AS b
            JOIN users AS u2 ON b.added_by = u2.id
        WHERE
            b.company_id = c.id
    )
SELECT
    (
        SELECT
            goods
        FROM
            goods_data AS goods
    ) AS goods,
    (
        SELECT
            clients
        FROM
            clients_data
    ) AS clients
FROM
    companies AS c
WHERE
    c.id = ?;

-- History refactor
WITH
    BillData AS (
        SELECT
            h.id,
            CASE
                WHEN h.type = 'Invoice' THEN 'INV-' || h.bill_num
                ELSE 'EST-' || h.bill_num
            END AS bill_num,
            h.bill_timestamp,
            h.type,
            COALESCE(b1.name, '') AS billed_to,
            COALESCE(b2.name, '') AS shipped_to,
            h.transport,
            h.payment,
            h.eta,
            h.amount
        FROM
            history AS h
            LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
            LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
        WHERE
            h.company_id = ?
    ),
    GoodsData AS (
        SELECT
            hg.history_id AS history_id,
            json_group_array (
                json_object (
                    'descp',
                    g.descp,
                    'hsn_sac',
                    g.hsn_sac,
                    'uom',
                    g.uom,
                    'rate',
                    g.rate,
                    'gst',
                    g.gst,
                    'qty',
                    hg.qty
                )
            ) AS goods_data
        FROM
            goods AS g
            LEFT JOIN history_goods AS hg ON g.id = hg.goods_id
    )
SELECT
    bd.id,
    bd.bill_num,
    bd.bill_timestamp,
    bd.type,
    bd.billed_to,
    bd.shipped_to,
    bd.transport,
    bd.payment,
    bd.eta,
    bd.amount,
    gd.goods_data AS list_of_goods
FROM
    BillData AS bd
    LEFT JOIN GoodsData AS gd ON bd.id = gd.history_id
GROUP BY
    bd.id,
    bd.bill_num,
    bd.bill_timestamp,
    bd.type,
    bd.billed_to,
    bd.shipped_to,
    bd.transport,
    bd.payment,
    bd.eta,
    bd.amount
ORDER BY
    bd.id DESC;

-- New Home query
WITH
    invoice_data AS (
        SELECT
            h.id,
            'INV-' || h.bill_num AS bill_num,
            h.bill_timestamp,
            COALESCE(b1.name, '') AS billed_to,
            COALESCE(b2.name, '') AS shipped_to,
            h.transport,
            h.payment,
            h.eta,
            h.amount,
            json_group_array (
                json_object (
                    'descp',
                    g.descp,
                    'hsn_sac',
                    g.hsn_sac,
                    'uom',
                    g.uom,
                    'rate',
                    g.rate,
                    'gst',
                    g.gst,
                    'qty',
                    hg.qty
                )
            ) AS list_of_goods
        FROM
            history AS h
            LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
            LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
            LEFT JOIN history_goods AS hg ON h.id = hg.history_id
            LEFT JOIN goods AS g ON hg.goods_id = g.id
        WHERE
            h.company_id = c.id
            AND h.type = 'Invoice'
        GROUP BY
            h.id,
            h.bill_num,
            h.bill_timestamp,
            billed_to,
            shipped_to,
            h.transport,
            h.payment,
            h.eta,
            h.amount
        ORDER BY
            h.id DESC
        LIMIT
            5
    ),
    quotation_data AS (
        SELECT
            h.id,
            'EST-' || h.bill_num AS bill_num,
            h.bill_timestamp,
            COALESCE(b1.name, '') AS billed_to,
            h.eta,
            h.amount,
            json_group_array (
                json_object (
                    'descp',
                    g.descp,
                    'hsn_sac',
                    g.hsn_sac,
                    'uom',
                    g.uom,
                    'rate',
                    g.rate,
                    'gst',
                    g.gst,
                    'qty',
                    hg.qty
                )
            ) AS list_of_goods
        FROM
            history AS h
            LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
            LEFT JOIN history_goods AS hg ON h.id = hg.history_id
            LEFT JOIN goods AS g ON hg.goods_id = g.id
        WHERE
            h.company_id = c.id
            AND h.type = 'Quotation'
        GROUP BY
            h.id,
            h.bill_num,
            h.bill_timestamp,
            billed_to,
            h.eta,
            h.amount
        ORDER BY
            h.id DESC
        LIMIT
            5
    )
SELECT
    (
        SELECT
            json_group_array (
                json_object (
                    'id',
                    id,
                    'bill_num',
                    bill_num,
                    'bill_timestamp',
                    bill_timestamp,
                    'billed_to',
                    billed_to,
                    'shipped_to',
                    shipped_to,
                    'transport',
                    transport,
                    'payment',
                    payment,
                    'eta',
                    eta,
                    'amount',
                    amount,
                    'list_of_goods',
                    list_of_goods
                )
            )
        FROM
            invoice_data
    ) AS invoices,
    (
        SELECT
            json_group_array (
                json_object (
                    'id',
                    id,
                    'bill_num',
                    bill_num,
                    'bill_timestamp',
                    bill_timestamp,
                    'billed_to',
                    billed_to,
                    'eta',
                    eta,
                    'amount',
                    amount,
                    'list_of_goods',
                    list_of_goods
                )
            )
        FROM
            quotation_data
    ) AS quotations
FROM
    companies AS c
WHERE
    c.id = ?;

-- New Home query codeium broken
SELECT
    json_group_array (
        json_object (
            'id',
            id,
            'bill_num',
            bill_num,
            'bill_timestamp',
            bill_timestamp,
            'billed_to',
            billed_to,
            'shipped_to',
            shipped_to,
            'transport',
            transport,
            'payment',
            payment,
            'eta',
            eta,
            'amount',
            amount,
            'list_of_goods',
            list_of_goods
        )
    ) AS invoices,
    json_group_array (
        json_object (
            'id',
            id,
            'bill_num',
            bill_num,
            'bill_timestamp',
            bill_timestamp,
            'billed_to',
            billed_to,
            'eta',
            eta,
            'amount',
            amount,
            'list_of_goods',
            list_of_goods
        )
    ) AS quotations
FROM
    (
        SELECT
            h.id,
            CASE
                WHEN h.type = 'Invoice' THEN 'INV-' || h.bill_num
                ELSE 'EST-' || h.bill_num
            END AS bill_num,
            h.bill_timestamp,
            COALESCE(b1.name, '') AS billed_to,
            COALESCE(b2.name, '') AS shipped_to,
            h.transport,
            h.payment,
            h.eta,
            h.amount,
            json_group_array (
                json_object (
                    'descp',
                    g.descp,
                    'hsn_sac',
                    g.hsn_sac,
                    'uom',
                    g.uom,
                    'rate',
                    g.rate,
                    'gst',
                    g.gst,
                    'qty',
                    hg.qty
                )
            ) AS list_of_goods,
            h.type
        FROM
            history AS h
            LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
            LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
            LEFT JOIN history_goods AS hg ON h.id = hg.history_id
            LEFT JOIN goods AS g ON hg.goods_id = g.id
        WHERE
            h.company_id = c.id
            AND (
                h.type = 'Invoice'
                OR h.type = 'Quotation'
            )
        GROUP BY
            h.id,
            h.bill_num,
            h.bill_timestamp,
            billed_to,
            shipped_to,
            h.transport,
            h.payment,
            h.eta,
            h.amount,
            h.type
        ORDER BY
            h.id DESC
        LIMIT
            5
    ) AS combined_data
    JOIN companies AS c ON c.id = ?
GROUP BY
    c.id;

-- New Home query
SELECT
    (
        SELECT
            json_group_array (
                json_object (
                    'id',
                    id,
                    'bill_num',
                    bill_num,
                    'bill_timestamp',
                    bill_timestamp,
                    'billed_to',
                    billed_to,
                    'shipped_to',
                    shipped_to,
                    'transport',
                    transport,
                    'payment',
                    payment,
                    'eta',
                    eta,
                    'amount',
                    amount,
                    'list_of_goods',
                    list_of_goods
                )
            )
        FROM
            (
                SELECT
                    h.id,
                    'INV-' || h.bill_num AS bill_num,
                    h.bill_timestamp,
                    COALESCE(b1.name, '') AS billed_to,
                    COALESCE(b2.name, '') AS shipped_to,
                    h.transport,
                    h.payment,
                    h.eta,
                    h.amount,
                    (
                        SELECT
                            json_group_array (
                                json_object (
                                    'descp',
                                    g.descp,
                                    'hsn_sac',
                                    g.hsn_sac,
                                    'uom',
                                    g.uom,
                                    'rate',
                                    g.rate,
                                    'gst',
                                    g.gst,
                                    'qty',
                                    hg.qty
                                )
                            )
                        FROM
                            history_goods AS hg
                            LEFT JOIN goods AS g ON hg.goods_id = g.id
                        WHERE
                            hg.history_id = h.id
                    ) AS list_of_goods
                FROM
                    history AS h
                    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
                    LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
                WHERE
                    h.company_id = c.id
                    AND h.type = 'Invoice'
                ORDER BY
                    h.id DESC
                LIMIT
                    5
            ) AS invoice_data
    ) as invoices,
    (
        SELECT
            json_group_array (
                json_object (
                    'id',
                    id,
                    'bill_num',
                    bill_num,
                    'bill_timestamp',
                    bill_timestamp,
                    'billed_to',
                    billed_to,
                    'eta',
                    eta,
                    'amount',
                    amount,
                    'list_of_goods',
                    list_of_goods
                )
            )
        FROM
            (
                SELECT
                    h.id,
                    'EST-' || h.bill_num AS bill_num,
                    h.bill_timestamp,
                    COALESCE(b1.name, '') AS billed_to,
                    h.eta,
                    h.amount,
                    (
                        SELECT
                            json_group_array (
                                json_object (
                                    'descp',
                                    g.descp,
                                    'hsn_sac',
                                    g.hsn_sac,
                                    'uom',
                                    g.uom,
                                    'rate',
                                    g.rate,
                                    'gst',
                                    g.gst,
                                    'qty',
                                    hg.qty
                                )
                            )
                        FROM
                            history_goods AS hg
                            LEFT JOIN goods AS g ON hg.goods_id = g.id
                        WHERE
                            hg.history_id = h.id
                    ) AS list_of_goods
                FROM
                    history AS h
                    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
                WHERE
                    h.company_id = c.id
                    AND h.type = 'Quotation'
                ORDER BY
                    h.id DESC
                LIMIT
                    5
            ) AS quotation_data
    ) as quotations
FROM
    companies AS c
WHERE
    c.id = ?;

-- History query
SELECT
    h.id,
    h.bill_num,
    h.bill_timestamp,
    h.type,
    b1.name AS billed_to,
    b2.name AS shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount,
    g.descp,
    g.hsn_sac,
    g.uom,
    g.rate,
    g.gst,
    hg.qty,
    hg.amount AS good_amount
FROM
    history AS h
    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
    LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
    LEFT JOIN history_goods AS hg ON h.id = hg.history_id
    LEFT JOIN goods AS g ON hg.goods_id = g.id
WHERE
    h.company_id = ?
ORDER BY
    h.id DESC;

-- Index query
SELECT
    h.id,
    h.bill_num,
    h.bill_timestamp,
    h.type,
    b1.name AS billed_to,
    b2.name AS shipped_to,
    h.transport,
    h.payment,
    h.eta,
    h.amount,
    g.descp,
    g.hsn_sac,
    g.uom,
    g.rate,
    g.gst,
    hg.qty,
    hg.amount AS good_amount
FROM
    (
        SELECT
            id
        FROM
            history
        WHERE
            company_id = ?
            AND type = ?
        ORDER BY
            id DESC
        LIMIT
            5
    ) AS distinct_ids
    JOIN history AS h ON distinct_ids.id = h.id
    LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
    LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
    LEFT JOIN history_goods AS hg ON h.id = hg.history_id
    LEFT JOIN goods AS g ON hg.goods_id = g.id;

-- Inventory query for goods
SELECT
    g.descp,
    g.hsn_sac,
    g.uom,
    g.rate,
    g.gst,
    g.added_at,
    u1.username AS added_by
FROM
    goods AS g
    JOIN users AS u1 ON g.added_by = u1.id
WHERE
    g.company_id = ?;