-- ============================================================
-- Schema for the Olist e-commerce data (SQLite; MySQL notes in README)
--
--   customers 1 --- * orders 1 --- * order_items * --- 1 products
--                       1
--                       |
--                       * payments
-- ============================================================

DROP VIEW  IF EXISTS sales;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id         VARCHAR(32) PRIMARY KEY,   -- one per order
    customer_unique_id  VARCHAR(32) NOT NULL,      -- one per real person (use this to find repeat buyers)
    customer_city       VARCHAR(60),
    customer_state      CHAR(2)
);

CREATE TABLE orders (
    order_id                       VARCHAR(32) PRIMARY KEY,
    customer_id                    VARCHAR(32) NOT NULL REFERENCES customers(customer_id),
    order_status                   VARCHAR(15) NOT NULL,
    order_purchase_timestamp       DATETIME    NOT NULL,
    order_delivered_customer_date  DATETIME,
    order_estimated_delivery_date  DATETIME
);

CREATE TABLE products (
    product_id  VARCHAR(32) PRIMARY KEY,
    category    VARCHAR(60) NOT NULL
);

CREATE TABLE order_items (
    order_id       VARCHAR(32) NOT NULL REFERENCES orders(order_id),
    order_item_id  INTEGER     NOT NULL,           -- 1, 2, 3... within an order
    product_id     VARCHAR(32) NOT NULL REFERENCES products(product_id),
    seller_id      VARCHAR(32) NOT NULL,
    price          DECIMAL(10, 2) NOT NULL,
    freight_value  DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE payments (
    order_id              VARCHAR(32) NOT NULL REFERENCES orders(order_id),
    payment_sequential    INTEGER     NOT NULL,
    payment_type          VARCHAR(20) NOT NULL,
    payment_installments  INTEGER     NOT NULL,
    payment_value         DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_items_product   ON order_items (product_id);
CREATE INDEX idx_payments_order  ON payments (order_id);


-- ------------------------------------------------------------
-- `sales` view: one row per item sold. THE revenue rule lives here:
--   * only DELIVERED orders count as revenue
--   * only complete months, Jan 2017 - Aug 2018
--   * revenue = item price; freight is kept in its own column
-- Every analysis query reads from this view, so the rule is applied
-- the same way everywhere.
-- ------------------------------------------------------------
CREATE VIEW sales AS
SELECT
    o.order_id,
    DATE(o.order_purchase_timestamp)             AS order_date,
    strftime('%Y-%m', o.order_purchase_timestamp) AS month,
    CAST(strftime('%w', o.order_purchase_timestamp) AS INTEGER) AS weekday,  -- 0 = Sunday
    c.customer_unique_id,
    c.customer_state                             AS state,
    i.product_id,
    p.category,
    i.price                                      AS revenue,
    i.freight_value                              AS freight
FROM order_items i
JOIN orders    o ON o.order_id    = i.order_id
JOIN customers c ON c.customer_id = o.customer_id
JOIN products  p ON p.product_id  = i.product_id
WHERE o.order_status = 'delivered'
  AND strftime('%Y-%m', o.order_purchase_timestamp) BETWEEN '2017-01' AND '2018-08';
