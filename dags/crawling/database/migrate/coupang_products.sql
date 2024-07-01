CREATE TABLE coupang_products (
    id SERIAL PRIMARY KEY,
    product_id BIGINT,
    title TEXT,
    price TEXT,
    per_price TEXT,
    star FLOAT,
    review_count TEXT,
    category_id BIGINT
);