CREATE TABLE users (
    id    SERIAL PRIMARY KEY,
    tg_id INTEGER NOT NULL UNIQUE,
    name  TEXT UNIQUE
);

CREATE TABLE products (
    id    SERIAL PRIMARY KEY,
    price DOUBLE PRECISION NOT NULL
);

CREATE TABLE payments (
    id         VARCHAR(255) NOT NULL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO products (id, price) VALUES 
    (1, 25.0),
    (2, 3.0);
