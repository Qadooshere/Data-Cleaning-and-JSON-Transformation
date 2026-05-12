"""
generate_demo_csvs.py
=====================
Creates a ./data/ folder with several realistic-but-messy CSV files
designed to test every cleaning and transformation step in csv_pipeline.py.

Each file intentionally contains problems the pipeline must fix:
  - Inconsistent column names
  - Mixed-case / extra whitespace values
  - Duplicate rows (some cross-file)
  - Null placeholders (N/A, null, -, empty string)
  - Mixed date formats
  - Numeric columns stored as strings
  - Varying delimiters (comma, semicolon, pipe)

Run:
    python generate_demo_csvs.py
    python csv_pipeline.py          # then run the pipeline to test it
"""

import os
import csv
from pathlib import Path

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)


# ── FILE 1: employees_us.csv  (comma-delimited, typical HR export) ──────────
employees_us = [
    ["EMP_ID", "FirstName", "LastName", "EmailAddress", "dept",    "Salary", "DOB",        "gender", "country"],
    ["001",    "Alice",     "Johnson",  "alice@co.com", "Sales",   "72000",  "1990-04-15", "F",      "USA"],
    ["002",    "Bob  ",     "Smith",    "BOB@CO.COM",   "IT",      "95000",  "1985-11-02", "male",   "usa"],
    ["003",    "Carol",     "White",    "carol@co.com", "HR",      "N/A",    "1992-07-23", "Female", "United States"],
    ["004",    "David",     "Brown",    "N/A",          "Sales",   "68000",  "1988-01-30", "m",      "US"],
    ["005",    "Eve",       "Davis",    "eve@co.com",   "Finance", "110000", "1995-03-12", "f",      "USA"],
    # Intentional duplicate of row 002
    ["002",    "Bob  ",     "Smith",    "BOB@CO.COM",   "IT",      "95000",  "1985-11-02", "male",   "usa"],
    # A fully empty row (pipeline should drop it)
    ["",       "",          "",         "",             "",        "",       "",           "",        ""],
    ["006",    "Frank",     "Miller",   "frank@co.com", "IT",      "88000",  "null",       "Man",    "United States"],
    ["007",    "Grace",     "Wilson",   "grace@co.com", "HR",      "71500",  "1993-06-18", "woman",  "USA"],
    ["008",    "Hank",      "Moore",    "hank@co.com",  "Finance", "?",      "1980-09-05", "male",   "USA"],
]

with open(DATA_DIR / "employees_us.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(employees_us)
print("Created: data/employees_us.csv")


# ── FILE 2: employees_eu.csv  (semicolon-delimited, European HR export) ─────
employees_eu = [
    ["emp_id", "full_name",       "mail",            "division",  "wage",   "dob",        "sex",    "nation"],
    ["101",    "Ingrid Hansen",   "ingrid@corp.de",  "IT",        "82000",  "15/04/1991", "female", "Germany"],
    ["102",    "Jacques Dupont",  "j.dupont@corp.fr","Finance",   "91000",  "22/08/1987", "male",   "France"],
    ["103",    "Layla Ahmed",     "layla@corp.ae",   "HR",        "-",      "03/12/1994", "f",      "UAE"],
    ["104",    "Marco Rossi",     "marco@corp.it",   "Sales",     "74000",  "09/05/1989", "m",      "Italy"],
    ["104",    "Marco Rossi",     "marco@corp.it",   "Sales",     "74000",  "09/05/1989", "m",      "Italy"],  # dup
    ["105",    "Nina Petrov",     "nina@corp.bg",    "IT",        "67000",  "18/03/1996", "female", "Bulgaria"],
    ["106",    "Oscar Svensson",  "oscar@corp.se",   "Finance",   "n/a",    "27/07/1982", "male",   "Sweden"],
    # Cross-file duplicate: same email as Alice in file 1 (pipeline dedup by email)
    ["107",    "Alice Johnson",   "alice@co.com",    "Sales",     "72000",  "15/04/1990", "F",      "USA"],
    ["108",    "Priya Sharma",    "priya@corp.in",   "IT",        "59000",  "11/11/1993", "Female", "India"],
]

with open(DATA_DIR / "employees_eu.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerows(employees_eu)
print("Created: data/employees_eu.csv")


# ── FILE 3: customers.csv  (pipe-delimited, CRM export) ─────────────────────
customers = [
    ["customer_id", "firstname", "lastname", "email",              "phone",         "city",         "country",   "score", "created"],
    ["C001",        "Amelia",    "Clarke",   "amelia@email.com",   "+44-7700-123",  "London",       "UK",        "8.5",   "2023-01-10"],
    ["C002",        "Bashir",    "Taleb",    "bashir@email.com",   "+1-555-0102",   "New York",     "USA",       "7.2",   "2023-02-14"],
    ["C003",        "Chen",      "Wei",      "chen.wei@email.com", "+86-131-0001",  "Shanghai",     "China",     "NULL",  "2023-03-05"],
    ["C004",        "Diana",     "Flores",   "diana@email.com",    "None",          "Mexico City",  "Mexico",    "9.1",   "2023-03-22"],
    ["C005",        "Elias",     "Berg",     "elias@email.com",    "+49-176-0003",  "Berlin",       "Germany",   "6.0",   "2023-04-01"],
    ["C006",        "Fatima",    "Nour",     "N/A",                "+20-100-0004",  "Cairo",        "egypt",     "8.8",   "invalid_date"],
    ["C007",        "George",    "Papadop",  "george@email.com",   "+30-697-0005",  "Athens",       "Greece",    "5.5",   "2023-05-17"],
    ["C007",        "George",    "Papadop",  "george@email.com",   "+30-697-0005",  "Athens",       "Greece",    "5.5",   "2023-05-17"],  # dup
    ["C008",        "Hannah",    "Kim",      "hannah@email.com",   "+82-10-0006",   "Seoul",        "South Korea","9.9",  "2023-06-02"],
    ["C009",        "Ivan",      "Petrov",   "ivan@email.com",     "+7-916-0007",   "Moscow",       "Russia",    "?",     "2023-06-15"],
    ["C010",        "Julia",     "Souza",    "julia@email.com",    "+55-11-0008",   "São Paulo",    "Brazil",    "7.7",   "2023-07-04"],
]

with open(DATA_DIR / "customers.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="|")
    writer.writerows(customers)
print("Created: data/customers.csv")


# ── FILE 4: performance_scores.csv  (tab-delimited, clean-ish data) ─────────
performance = [
    ["id",   "email",              "score", "rating",  "department", "review_date"],
    ["001",  "alice@co.com",       "88",    "Exceeds",  "Sales",     "2024-01-15"],
    ["002",  "bob@co.com",         "76",    "Meets",    "IT",        "2024-01-15"],
    ["003",  "carol@co.com",       "91",    "Exceeds",  "HR",        "2024-01-16"],
    ["004",  "david@co.com",       "N/A",   "N/A",      "Sales",     "2024-01-16"],
    ["005",  "eve@co.com",         "95",    "Exceeds",  "Finance",   "2024-01-17"],
    ["006",  "frank@co.com",       "82",    "Meets",    "IT",        "2024-01-17"],
    ["101",  "ingrid@corp.de",     "79",    "Meets",    "IT",        "2024-01-18"],
    ["102",  "j.dupont@corp.fr",   "85",    "Exceeds",  "Finance",   "2024-01-18"],
    ["105",  "nina@corp.bg",       "70",    "Meets",    "IT",        "2024-01-19"],
    ["108",  "priya@corp.in",      "93",    "Exceeds",  "IT",        "2024-01-19"],
    # Some IDs with no match in other files (orphan records – good edge case)
    ["999",  "orphan@nowhere.com", "60",    "Below",    "Unknown",   "2024-01-20"],
]

with open(DATA_DIR / "performance_scores.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerows(performance)
print("Created: data/performance_scores.csv")


print(f"\n✓ All demo CSVs created in '{DATA_DIR.resolve()}'")
print("  Now run:  python csv_pipeline.py")
print("  Output:   master_output.json")
