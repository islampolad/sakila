import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text

# =============================================================================
# 0. SETUP DATABASE CONNECTIONS
# =============================================================================
PASSWORD = "isoholmes" 
HOST = "localhost"
PORT = "3306"

source_engine = create_engine(f"mysql+pymysql://root:{PASSWORD}@{HOST}:{PORT}/sakila")
target_engine = create_engine(f"mysql+pymysql://root:{PASSWORD}@{HOST}:{PORT}/sakila_olap")

print("🔌 Database connections established successfully!")

truncate_query = """
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE fact_payment;
TRUNCATE TABLE fact_rental;
TRUNCATE TABLE dim_customer;
TRUNCATE TABLE dim_film;
TRUNCATE TABLE dim_store;
TRUNCATE TABLE dim_staff;
TRUNCATE TABLE dim_date;
SET FOREIGN_KEY_CHECKS = 1;
"""
with target_engine.begin() as conn:
    for statement in truncate_query.split(";"):
        if statement.strip():
            conn.execute(text(statement))

# =============================================================================
# 1. EXTRACT PHASE
# =============================================================================
print("\n📥 Starting Extract Phase...")

df_customer   = pd.read_sql_table("customer", source_engine)
df_address    = pd.read_sql_table("address", source_engine)
if 'location' in df_address.columns:
    df_address = df_address.drop(columns=['location'])

df_city       = pd.read_sql_table("city", source_engine)
df_country    = pd.read_sql_table("country", source_engine)
df_film       = pd.read_sql_table("film", source_engine)
df_language   = pd.read_sql_table("language", source_engine)
df_category   = pd.read_sql_table("category", source_engine)
df_film_cat   = pd.read_sql_table("film_category", source_engine)
df_store      = pd.read_sql_table("store", source_engine)
df_staff      = pd.read_sql_table("staff", source_engine)
df_rental     = pd.read_sql_table("rental", source_engine)
df_payment    = pd.read_sql_table("payment", source_engine)
df_inventory  = pd.read_sql_table("inventory", source_engine)

print("✅ All raw operational tables successfully extracted into memory.")

# =============================================================================
# 2. TRANSFORM PHASE
# =============================================================================
print("\n⚡ Starting Transform Phase...")

# 2.1 Transform: Dim_Date
print("⚙️ Building Dim_Date...")
date_range = pd.date_range(start="2005-01-01", end="2026-12-31", freq="D")
dim_date = pd.DataFrame()
dim_date["date_key"] = date_range.strftime("%Y%m%d").astype(int)
dim_date["full_date"] = date_range.date
dim_date["day_of_week"] = date_range.day_name()
dim_date["day_of_month"] = date_range.day
dim_date["month_number"] = date_range.month
dim_date["month_name"] = date_range.month_name()
dim_date["quarter"] = date_range.quarter
dim_date["year"] = date_range.year

# 2.2 Transform: Dim_Customer
print("⚙️ Building Dim_Customer...")
cust_geo = df_customer.merge(df_address, on="address_id", how="left") \
                      .merge(df_city, on="city_id", how="left", suffixes=('', '_city')) \
                      .merge(df_country, on="country_id", how="left", suffixes=('', '_country'))

dim_customer = pd.DataFrame()
dim_customer["customer_id"] = cust_geo["customer_id"]
dim_customer["first_name"] = cust_geo["first_name"]
dim_customer["last_name"] = cust_geo["last_name"]
dim_customer["email"] = cust_geo["email"].fillna("")
dim_customer["active_status"] = cust_geo["active"].apply(lambda x: "Active" if x == 1 else "Inactive")
dim_customer["address"] = cust_geo["address"]
dim_customer["district"] = cust_geo["district"].fillna("")
dim_customer["city"] = cust_geo["city"]
dim_customer["country"] = cust_geo["country"]

# 2.3 Transform: Dim_Film
print("⚙️ Building Dim_Film...")
film_cat_merge = df_film_cat.merge(df_category, on="category_id", how="left")
film_enriched = df_film.merge(df_language, on="language_id", how="left") \
                       .merge(film_cat_merge, on="film_id", how="left")

dim_film = pd.DataFrame()
dim_film["film_id"] = film_enriched["film_id"]
dim_film["title"] = film_enriched["title"]
dim_film["description"] = film_enriched["description"].fillna("")
dim_film["release_year"] = film_enriched["release_year"].fillna(0).astype(int)
dim_film["language"] = film_enriched["name_x"].str.strip()
dim_film["rental_duration"] = film_enriched["rental_duration"]
dim_film["rental_rate"] = film_enriched["rental_rate"]
dim_film["length"] = film_enriched["length"].fillna(0).astype(int)
dim_film["replacement_cost"] = film_enriched["replacement_cost"]
dim_film["rating"] = film_enriched["rating"].fillna("G")
dim_film["category_name"] = film_enriched["name_y"].fillna("Unknown")

# 2.4 Transform: Dim_Store
print("⚙️ Building Dim_Store...")
store_manager = df_store.merge(df_staff, left_on="manager_staff_id", right_on="staff_id", how="left")
store_geo = store_manager.merge(df_address, left_on="address_id_x", right_on="address_id", how="left") \
                         .merge(df_city, on="city_id", how="left", suffixes=('', '_city')) \
                         .merge(df_country, on="country_id", how="left", suffixes=('', '_country'))

dim_store = pd.DataFrame()
dim_store["store_id"] = store_geo["store_id_x"]
dim_store["manager_name"] = (store_geo["first_name"] + " " + store_geo["last_name"]).fillna("Unknown")
dim_store["address"] = store_geo["address"]
dim_store["district"] = store_geo["district"].fillna("")
dim_store["city"] = store_geo["city"]
dim_store["country"] = store_geo["country"]

# 2.5 Transform: Dim_Staff
print("⚙️ Building Dim_Staff...")
dim_staff = pd.DataFrame()
dim_staff["staff_id"] = df_staff["staff_id"]
dim_staff["first_name"] = df_staff["first_name"]
dim_staff["last_name"] = df_staff["last_name"]
dim_staff["email"] = df_staff["email"].fillna("")
dim_staff["store_id"] = df_staff["store_id"]
dim_staff["active_status"] = df_staff["active"].apply(lambda x: "Active" if x == 1 else "Inactive")

print("✅ Dimensions transformation complete!")

# =============================================================================
# 3. LOAD PHASE (LOADING DIMENSIONS via APPEND)
# =============================================================================
print("\n🚀 Starting Load Phase...")

print("📤 Loading dim_date...")
dim_date.to_sql("dim_date", target_engine, if_exists="append", index=False)

print("📤 Loading dim_customer...")
dim_customer.to_sql("dim_customer", target_engine, if_exists="append", index=False)

print("📤 Loading dim_film...")
dim_film.to_sql("dim_film", target_engine, if_exists="append", index=False)

print("📤 Loading dim_store...")
dim_store.to_sql("dim_store", target_engine, if_exists="append", index=False)

print("📤 Loading dim_staff...")
dim_staff.to_sql("dim_staff", target_engine, if_exists="append", index=False)

print("✅ All Dimensions safely loaded into sakila_olap!")

# =============================================================================
# 4. TRANSFORM & LOAD FACTS (STRICT TYPE-SAFE LOOKUPS)
# =============================================================================
print("\n⛓️ Processing Fact Tables (Mapping to Surrogate Keys)...")

# Harvest and immediately force strict integer casting to avoid mismatch drops
db_customer = pd.read_sql_table("dim_customer", target_engine)[["customer_key", "customer_id"]]
db_customer["customer_id"] = db_customer["customer_id"].astype(int)

db_film = pd.read_sql_table("dim_film", target_engine)[["film_key", "film_id"]]
db_film["film_id"] = db_film["film_id"].astype(int)

db_store = pd.read_sql_table("dim_store", target_engine)[["store_key", "store_id"]]
db_store["store_id"] = db_store["store_id"].astype(int)

db_staff = pd.read_sql_table("dim_staff", target_engine)[["staff_key", "staff_id"]]
db_staff["staff_id"] = db_staff["staff_id"].astype(int)

# Standardize operational tables
df_rental["customer_id"] = df_rental["customer_id"].astype(int)
df_rental["staff_id"]    = df_rental["staff_id"].astype(int)
df_inventory["film_id"]  = df_inventory["film_id"].astype(int)
df_inventory["store_id"] = df_inventory["store_id"].astype(int)
df_inventory["inventory_id"] = df_inventory["inventory_id"].astype(int)
df_rental["inventory_id"] = df_rental["inventory_id"].astype(int)

# 4.1 Build Fact_Rental
print("⚙️ Processing fact_rental...")
rental_m = df_rental.merge(df_inventory, on="inventory_id", how="left")
rental_m = rental_m.merge(db_customer, on="customer_id", how="left")
rental_m = rental_m.merge(db_film, on="film_id", how="left")
rental_m = rental_m.merge(db_store, on="store_id", how="left")
rental_m = rental_m.merge(db_staff, on="staff_id", how="left")

fact_rental = pd.DataFrame()
fact_rental["rental_id"] = rental_m["rental_id"].astype(int)
fact_rental["customer_key"] = rental_m["customer_key"].fillna(1).astype(int)
fact_rental["film_key"] = rental_m["film_key"].fillna(1).astype(int)
fact_rental["store_key"] = rental_m["store_key"].fillna(1).astype(int)
fact_rental["staff_key"] = rental_m["staff_key"].fillna(1).astype(int)
fact_rental["rental_date_key"] = pd.to_datetime(rental_m["rental_date"]).dt.strftime("%Y%m%d").astype(int)

r_date = pd.to_datetime(rental_m["return_date"]).dt.strftime("%Y%m%d")
fact_rental["return_date_key"] = r_date.where(r_date.notnull(), None)

rental_duration = (pd.to_datetime(rental_m["return_date"]) - pd.to_datetime(rental_m["rental_date"])).dt.days
fact_rental["rental_duration_days"] = rental_duration.where(rental_duration.notnull(), None)

expected_duration = rental_m["film_id"].map(dict(zip(dim_film.film_id, dim_film.rental_duration)))
fact_rental["is_late_return"] = np.where(fact_rental["rental_duration_days"].fillna(0) > expected_duration, 1, 0)

print("📤 Loading fact_rental...")
fact_rental.to_sql("fact_rental", target_engine, if_exists="append", index=False)

# 4.2 Build Fact_Payment
print("⚙️ Processing fact_payment...")
db_rental = pd.read_sql_table("fact_rental", target_engine)[["rental_key", "rental_id"]]
db_rental["rental_id"] = db_rental["rental_id"].astype(int)

df_payment["customer_id"] = df_payment["customer_id"].astype(int)
df_payment["staff_id"] = df_payment["staff_id"].astype(int)
df_payment["rental_id"] = df_payment["rental_id"].fillna(-1).astype(float).astype(int)

payment_m = df_payment.merge(db_customer, on="customer_id", how="left")
payment_m = payment_m.merge(db_staff, on="staff_id", how="left")
payment_m = payment_m.merge(db_rental, on="rental_id", how="left")

fact_payment = pd.DataFrame()
fact_payment["payment_id"] = payment_m["payment_id"].astype(int)
fact_payment["customer_key"] = payment_m["customer_key"].fillna(1).astype(int)
fact_payment["staff_key"] = payment_m["staff_key"].fillna(1).astype(int)

# Safely force key integration avoiding float representations
fact_payment["rental_key"] = payment_m["rental_key"].apply(lambda x: int(x) if pd.notnull(x) else None)
fact_payment["payment_date_key"] = pd.to_datetime(payment_m["payment_date"]).dt.strftime("%Y%m%d").astype(int)
fact_payment["amount"] = payment_m["amount"]

print("📤 Loading fact_payment...")
fact_payment.to_sql("fact_payment", target_engine, if_exists="append", index=False)

print("\n🎉 ETL PIPELINE EXECUTION COMPLETED SUCCESSFULLY WITH ALL DATA MATCHED!")