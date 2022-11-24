DROP table if exists users;
DROP table if exists products;
DROP table if exists cart;
DROP table if exists profiles;
DROP TABLE if exists product_parameters;
DROP TABLE if exists favourite;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login varchar(20) NOT NULL,
    email varchar(20),
    phone varchar(11) NOT NULL,
    password varchar(100) NOT NULL
    );

CREATE TABLE profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name varchar(40) NOT NULL,
    profile_image varchar(20),
    description varchar(300),
    FOREIGN KEY (user_id) REFERENCES users(id));

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name varchar(100) NOT NULL,
    product_image varchar(20),
    price INTEGER NOT NULL,
    description varchar(300) NOT NULL);

CREATE TABLE product_parameters(
    p_id REFERENCES products(product_id),
    radius INTEGER NOT NULL,
    width REAL NOT NULL,
    stud INTEGER NOT NULL, /* stud - number of fasteners that hold on the wheels */
    pcd INTEGER NOT NULL, /* pcd - pitch circle diameter */
    maker varchar(30) NOT NULL,
    type varchar(20) NOT NULL
);
CREATE TABLE cart(
    user_id REFERENCES users(id),
    pic_id REFERENCES products(product_id) /* pic - product in cart */
);
CREATE table favourite(
    user_id REFERENCES users(id),
    pic_id REFERENCES products(product_id)
)
