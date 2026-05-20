README.md

# Sakila Movie Rental Data Warehouse & ETL Pipeline

An end-to-end Data Engineering project that transforms the operational, highly normalized **Sakila OLTP database** into an optimized, high-performance analytical **OLAP Data Warehouse (Star Schema)**. 

While the core project requirements focused primarily on architecture and dimensional design, this repository contains a **fully functional physical implementation**, including the automated Python ETL execution script and explicit target schema definitions.

---

## 🚀 Project Overview & Architecture

Transactional systems (OLTP) are built for rapid daily data entry but perform poorly during complex analytical queries. This project restructures data to isolate analytical workloads, eliminate heavy table joins, and provide business managers with instant insights into revenue trends, store tracking, and inventory performance.

The target database architecture relies on a **Star Schema** deployment centered around two specialized operational processes:
* **`fact_rental`**: Captures distinct movie rental events, track fulfillment timeliness, and flags late returns.
* **`fact_payment`**: Captures cash flow transactions, individual customer processing invoices, and revenue metrics.

---

## 🛠️ Repository Structure

* 📂 **`Sakila_Data_Warehouse_Report.pdf`** (or `.docx`): The formal documentation answering the conceptual business questions, grain determinations, and design justifications.
* 📜 **`sakila_olap_schema.sql`**: The MySQL DDL script defining the physical target warehouse tables, primary keys, and exact foreign key references.
* 🐍 **`etl_process.py`**: The complete automated Python migration script containing the Extract, Transform, and Load engineering logic.

---

## ⚙️ ETL Pipeline Implementation Details

The ETL pipeline was constructed using **Python (Pandas, SQLAlchemy, PyMySQL)** to systematically clean and migrate data from the operational source into the data warehouse.

### 1. Extract Phase
Extracts data directly out of 11 distinct transactional source tables (`rental`, `payment`, `customer`, `film`, `inventory`, `store`, `staff`, `address`, `city`, `country`, `category`, and `film_category`).

### 2. Transform Phase
* **Surrogate Key Mapping:** Translates database-generated auto-incrementing identity values dynamically to map relationships securely.
* **Type-Safe Alignment:** Strictly enforces uniform integer casting across keys to prevent data dropouts or silent merge mismatches.
* **Feature Engineering:** Compares structural metrics to compute fields like `rental_duration_days` and calculate boolean states like `is_late_return` on the fly.
* **Data Cleaning:** Handles outstanding rental entries (`NULL` return dates) seamlessly and supplies fallback strings for missing data parameters.
* **System Workarounds:** Implements lower-case table configurations to bypass cross-platform database case-sensitivity quirks.

### 3. Load Phase
Employs precise truncation routines respecting table order constraints, loads dimensions seamlessly first via append operations, tracks generated surrogates, and secures fact loading boundaries cleanly.

---

## 💻 Tech Stack & Requirements

* **Database Engine:** MySQL Server 8.0+
* **Development Environment:** Visual Studio / VS Code
* **Language Runtime:** Python 3.10+
* **Required Libraries:**
  ```bash
  pip install pandas numpy sqlalchemy pymysql
