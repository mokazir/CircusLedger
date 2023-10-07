-- Old index query for invoice
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

-- Old index query for quotation
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

-- New index query Common
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

-- Old history query
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

-- New history query
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