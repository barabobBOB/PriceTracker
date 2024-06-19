CREATE TABLE coupang_products (
    id SERIAL PRIMARY KEY,
    product_id BIGINT,
    title TEXT,
    price BIGINT,
    per_price BIGINT,
    star FLOAT,
    review_count BIGINT,
    category_id BIGINT
);