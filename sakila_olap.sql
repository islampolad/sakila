CREATE DATABASE IF NOT EXISTS sakila_olap;
USE sakila_olap;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE Fact_Payment;
TRUNCATE TABLE Fact_Rental;
TRUNCATE TABLE Dim_Customer;
TRUNCATE TABLE Dim_Film;
TRUNCATE TABLE Dim_Store;
TRUNCATE TABLE Dim_Staff;
TRUNCATE TABLE Dim_Date;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Create Dimension: Date
CREATE TABLE Dim_Date (
    date_key INT PRIMARY KEY, -- Format: YYYYMMDD
    full_date DATE NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    day_of_month INT NOT NULL,
    month_number INT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL
);

-- 2. Create Dimension: Customer
CREATE TABLE Dim_Customer (
    customer_key INT AUTO_INCREMENT PRIMARY KEY, -- Surrogate Key
    customer_id SMALLINT UNSIGNED NOT NULL,       -- OLTP Business Key
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    email VARCHAR(50),
    active_status VARCHAR(10) NOT NULL,
    address VARCHAR(50) NOT NULL,
    district VARCHAR(20) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- 3. Create Dimension: Film
CREATE TABLE Dim_Film (
    film_key INT AUTO_INCREMENT PRIMARY KEY,     -- Surrogate Key
    film_id SMALLINT UNSIGNED NOT NULL,          -- OLTP Business Key
    title VARCHAR(128) NOT NULL,
    description TEXT,
    release_year YEAR,
    language VARCHAR(20) NOT NULL,
    rental_duration TINYINT UNSIGNED NOT NULL,
    rental_rate DECIMAL(4,2) NOT NULL,
    length SMALLINT UNSIGNED,
    replacement_cost DECIMAL(5,2) NOT NULL,
    rating VARCHAR(10),
    category_name VARCHAR(25) NOT NULL
);

-- 4. Create Dimension: Store
CREATE TABLE Dim_Store (
    store_key INT AUTO_INCREMENT PRIMARY KEY,     -- Surrogate Key
    store_id TINYINT UNSIGNED NOT NULL,           -- OLTP Business Key
    manager_name VARCHAR(90) NOT NULL,
    address VARCHAR(50) NOT NULL,
    district VARCHAR(20) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- 5. Create Dimension: Staff
CREATE TABLE Dim_Staff (
    staff_key INT AUTO_INCREMENT PRIMARY KEY,     -- Surrogate Key
    staff_id TINYINT UNSIGNED NOT NULL,           -- OLTP Business Key
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    email VARCHAR(50),
    store_id TINYINT UNSIGNED NOT NULL,
    active_status VARCHAR(10) NOT NULL
);

-- 6. Create Fact: Rental
CREATE TABLE Fact_Rental (
    rental_key INT AUTO_INCREMENT PRIMARY KEY,
    rental_id INT NOT NULL,                       -- OLTP Transaction Key
    customer_key INT NOT NULL,
    film_key INT NOT NULL,
    store_key INT NOT NULL,
    staff_key INT NOT NULL,
    rental_date_key INT NOT NULL,
    return_date_key INT,                          -- Can be NULL if not returned yet
    rental_duration_days INT,
    is_late_return TINYINT(1) DEFAULT 0,
    FOREIGN KEY (customer_key) REFERENCES Dim_Customer(customer_key),
    FOREIGN KEY (film_key) REFERENCES Dim_Film(film_key),
    FOREIGN KEY (store_key) REFERENCES Dim_Store(store_key),
    FOREIGN KEY (staff_key) REFERENCES Dim_Staff(staff_key),
    FOREIGN KEY (rental_date_key) REFERENCES Dim_Date(date_key)
);

-- 7. Create Fact: Payment
CREATE TABLE Fact_Payment (
    payment_key INT AUTO_INCREMENT PRIMARY KEY,
    payment_id SMALLINT UNSIGNED NOT NULL,        -- OLTP Transaction Key
    customer_key INT NOT NULL,
    staff_key INT NOT NULL,
    rental_key INT,                               -- Connects payments to rentals if applicable
    payment_date_key INT NOT NULL,
    amount DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (customer_key) REFERENCES Dim_Customer(customer_key),
    FOREIGN KEY (staff_key) REFERENCES Dim_Staff(staff_key),
    FOREIGN KEY (payment_date_key) REFERENCES Dim_Date(date_key)
);