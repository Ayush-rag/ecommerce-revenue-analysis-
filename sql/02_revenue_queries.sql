-- ============================================================
-- Revenue analysis queries. Each starts with "-- name: <name>"
-- so Python can run them one by one and save the results.
-- All revenue figures come from the `sales` view (delivered
-- orders, Jan 2017 - Aug 2018). Amounts are in Brazilian reais (R$).
--
--   AOV (average order value) = revenue / orders
--   MoM growth = change vs the previous month
--   YoY growth = change vs the same month a year earlier
-- ============================================================


-- name: overall_kpis
-- Headline numbers for the whole 20 months
SELECT
    ROUND(SUM(revenue), 2)                                      AS revenue,
    COUNT(DISTINCT order_id)                                    AS orders,
    COUNT(*)                                                    AS items_sold,
    COUNT(DISTINCT customer_unique_id)                          AS customers,
    ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2)           AS avg_order_value,
    ROUND(1.0 * COUNT(*) / COUNT(DISTINCT order_id), 2)         AS items_per_order,
    ROUND(SUM(freight), 2)                                      AS freight,
    ROUND(100.0 * SUM(freight) / SUM(revenue), 1)               AS freight_pct_of_revenue
FROM sales;


-- name: monthly_revenue
-- Revenue every month, with month-on-month and year-on-year growth
WITH monthly AS (
    SELECT
        month,
        SUM(revenue)              AS revenue,
        COUNT(DISTINCT order_id)  AS orders
    FROM sales
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 2)                                                     AS revenue,
    orders,
    ROUND(revenue / orders, 2)                                            AS avg_order_value,
    ROUND(100.0 * (revenue - LAG(revenue) OVER w) / LAG(revenue) OVER w, 1)         AS mom_growth_pct,
    ROUND(100.0 * (revenue - LAG(revenue, 12) OVER w) / LAG(revenue, 12) OVER w, 1) AS yoy_growth_pct
FROM monthly
WINDOW w AS (ORDER BY month)
ORDER BY month;


-- name: year_comparison
-- Like-for-like: January-August 2017 vs January-August 2018
SELECT
    substr(month, 1, 4)                                AS year,
    ROUND(SUM(revenue), 2)                             AS revenue_jan_aug,
    COUNT(DISTINCT order_id)                           AS orders_jan_aug,
    ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2)  AS avg_order_value
FROM sales
WHERE substr(month, 6, 2) BETWEEN '01' AND '08'
GROUP BY year
ORDER BY year;


-- name: category_revenue
-- Revenue by product category, with each category's share and the running
-- (cumulative) share - the basis of the Pareto / 80-20 analysis
WITH cat AS (
    SELECT
        category,
        SUM(revenue)              AS revenue,
        COUNT(DISTINCT order_id)  AS orders,
        COUNT(*)                  AS items_sold
    FROM sales
    GROUP BY category
)
SELECT
    RANK() OVER (ORDER BY revenue DESC)                                   AS revenue_rank,
    category,
    ROUND(revenue, 2)                                                     AS revenue,
    orders,
    items_sold,
    ROUND(revenue / items_sold, 2)                                        AS avg_item_price,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2)                      AS share_pct,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC
                                     ROWS UNBOUNDED PRECEDING)
          / SUM(revenue) OVER (), 2)                                      AS cumulative_share_pct
FROM cat
ORDER BY revenue DESC;


-- name: product_pareto
-- How few products bring in 80% of revenue?
WITH prod AS (
    SELECT product_id, SUM(revenue) AS revenue
    FROM sales
    GROUP BY product_id
),
ranked AS (
    SELECT
        revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
            - revenue                                   AS revenue_before,
        SUM(revenue) OVER ()                            AS total
    FROM prod
)
SELECT
    COUNT(*)                                                         AS products_sold,
    SUM(CASE WHEN revenue_before < 0.8 * total THEN 1 ELSE 0 END)    AS products_for_80pct_revenue,
    ROUND(100.0 * SUM(CASE WHEN revenue_before < 0.8 * total THEN 1 ELSE 0 END)
          / COUNT(*), 1)                                             AS pct_of_products
FROM ranked;


-- name: state_revenue
-- Revenue by customer state (Brazil has 27 states)
SELECT
    state,
    ROUND(SUM(revenue), 2)                                  AS revenue,
    COUNT(DISTINCT order_id)                                AS orders,
    COUNT(DISTINCT customer_unique_id)                      AS customers,
    ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2)       AS avg_order_value,
    ROUND(100.0 * SUM(freight) / SUM(revenue), 1)           AS freight_pct_of_revenue,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS share_pct
FROM sales
GROUP BY state
ORDER BY revenue DESC;


-- name: weekday_revenue
-- Which day of the week sells most? (0 = Sunday)
SELECT
    weekday,
    CASE weekday WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue' WHEN 3 THEN 'Wed'
                 WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri' ELSE 'Sat' END    AS day,
    ROUND(SUM(revenue), 2)                                             AS revenue,
    COUNT(DISTINCT order_id)                                           AS orders,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2)         AS share_pct
FROM sales
GROUP BY weekday
ORDER BY CASE weekday WHEN 0 THEN 7 ELSE weekday END;


-- name: top_days
-- The 5 biggest sales days (look for Black Friday)
SELECT
    order_date,
    ROUND(SUM(revenue), 2)    AS revenue,
    COUNT(DISTINCT order_id)  AS orders
FROM sales
GROUP BY order_date
ORDER BY revenue DESC
LIMIT 5;


-- name: customer_loyalty
-- How many customers come back? Customers grouped by how many orders they placed
WITH per_customer AS (
    SELECT
        customer_unique_id,
        COUNT(DISTINCT order_id)  AS orders,
        SUM(revenue)              AS revenue
    FROM sales
    GROUP BY customer_unique_id
)
SELECT
    CASE WHEN orders = 1 THEN '1 order'
         WHEN orders = 2 THEN '2 orders'
         ELSE '3+ orders' END                                       AS customer_group,
    COUNT(*)                                                        AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)              AS customers_pct,
    ROUND(SUM(revenue), 2)                                          AS revenue,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2)      AS revenue_pct
FROM per_customer
GROUP BY customer_group
ORDER BY customer_group;


-- name: payment_methods
-- How customers pay (payment value includes freight, so it is a little
-- higher than item revenue)
SELECT
    p.payment_type,
    COUNT(DISTINCT p.order_id)                                         AS orders,
    ROUND(SUM(p.payment_value), 2)                                     AS amount_paid,
    ROUND(100.0 * SUM(p.payment_value) / SUM(SUM(p.payment_value)) OVER (), 2) AS share_pct,
    ROUND(AVG(p.payment_installments), 1)                              AS avg_installments
FROM payments p
WHERE p.order_id IN (SELECT DISTINCT order_id FROM sales)
GROUP BY p.payment_type
ORDER BY amount_paid DESC;
