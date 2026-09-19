import sqlite3

DB_PATH = "employee.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS EMPLOYEE(
    EMP_NAME VARCHAR(25),
    EMP_ID VARCHAR(25) PRIMARY KEY,
    DESIGNATION VARCHAR(25),
    EMP_AGE INT
)
""")

records = [
    ("Satish", "XY012", "NLP Engineer", 28),
    ("Aditya", "XY014", "Data Engineer", 35),
    ("Akshay", "XY013", "Data Scientist", 32),
    ("amith", "XY011", "Cloud Engineer", 38),
    ("Arun", "XY016", "Data Engineer", 45),
]

cursor.executemany("""
INSERT OR IGNORE INTO EMPLOYEE (EMP_NAME, EMP_ID, DESIGNATION, EMP_AGE)
VALUES (?, ?, ?, ?)
""", records)

connection.commit()

print("Employee records:")
for row in cursor.execute("SELECT * FROM EMPLOYEE ORDER BY EMP_ID"):
    print(row)

connection.close()
