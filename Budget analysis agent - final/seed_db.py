import os
import sqlite3

DB_PATH = os.environ.get(
    "BUDGET_AGENT_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "transactions.db")
)

def extract_month(date_str):
    if not date_str:
        return None
    return date_str[:7]

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Reset table for fresh testing
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            month TEXT,
            merchant TEXT,
            description TEXT,
            category TEXT,
            amount REAL,
            source_file TEXT
        )
    """)
    
    transactions = [
        # April 2026 (HDFC_April.csv)
        ("2026-04-01", "RENT PAYMENT LANDLORD", "RENT PAYMENT LANDLORD", "Housing", 18000.0, "HDFC_April.csv"),
        ("2026-04-02", "AMAZON PAY INDIA", "AMAZON PAY INDIA", "Shopping", 1899.0, "HDFC_April.csv"),
        ("2026-04-03", "SWIGGY BANGALORE", "SWIGGY BANGALORE", "Food & Dining", 380.0, "HDFC_April.csv"),
        ("2026-04-04", "UBER TRIP", "UBER TRIP", "Transportation", 290.0, "HDFC_April.csv"),
        ("2026-04-05", "BIGBASKET GROCERY", "BIGBASKET GROCERY", "Groceries", 1850.0, "HDFC_April.csv"),
        ("2026-04-07", "NETFLIX SUBSCRIPTION", "NETFLIX SUBSCRIPTION", "Subscriptions", 499.0, "HDFC_April.csv"),
        ("2026-04-08", "ELECTRICITY BOARD", "ELECTRICITY BOARD", "Utilities", 1320.0, "HDFC_April.csv"),
        ("2026-04-10", "SPOTIFY PREMIUM", "SPOTIFY PREMIUM", "Subscriptions", 119.0, "HDFC_April.csv"),
        ("2026-04-12", "ZOMATO ORDER", "ZOMATO ORDER", "Food & Dining", 540.0, "HDFC_April.csv"),
        ("2026-04-14", "CULT FIT MEMBERSHIP", "CULT FIT MEMBERSHIP", "Subscriptions", 1499.0, "HDFC_April.csv"),
        ("2026-04-16", "AMAZON PAY INDIA", "AMAZON PAY INDIA", "Shopping", 3200.0, "HDFC_April.csv"),
        ("2026-04-18", "OLA CABS", "OLA CABS", "Transportation", 210.0, "HDFC_April.csv"),
        ("2026-04-20", "RELIANCE FRESH", "RELIANCE FRESH", "Groceries", 980.0, "HDFC_April.csv"),
        ("2026-04-22", "PVR CINEMAS", "PVR CINEMAS", "Entertainment", 650.0, "HDFC_April.csv"),
        ("2026-04-25", "AIRTEL BROADBAND", "AIRTEL BROADBAND", "Utilities", 999.0, "HDFC_April.csv"),

        # May 2026 (HDFC_May.csv)
        ("2026-05-01", "RENT PAYMENT LANDLORD", "RENT PAYMENT LANDLORD", "Housing", 18000.0, "HDFC_May.csv"),
        ("2026-05-02", "AMAZON PAY INDIA", "AMAZON PAY INDIA", "Shopping", 2450.0, "HDFC_May.csv"),
        ("2026-05-03", "SWIGGY BANGALORE", "SWIGGY BANGALORE", "Food & Dining", 610.0, "HDFC_May.csv"),
        ("2026-05-04", "UBER TRIP", "UBER TRIP", "Transportation", 340.0, "HDFC_May.csv"),
        ("2026-05-06", "BIGBASKET GROCERY", "BIGBASKET GROCERY", "Groceries", 2100.0, "HDFC_May.csv"),
        ("2026-05-07", "NETFLIX SUBSCRIPTION", "NETFLIX SUBSCRIPTION", "Subscriptions", 499.0, "HDFC_May.csv"),
        ("2026-05-09", "ELECTRICITY BOARD", "ELECTRICITY BOARD", "Utilities", 1580.0, "HDFC_May.csv"),
        ("2026-05-10", "SPOTIFY PREMIUM", "SPOTIFY PREMIUM", "Subscriptions", 119.0, "HDFC_May.csv"),
        ("2026-05-11", "ZOMATO ORDER", "ZOMATO ORDER", "Food & Dining", 720.0, "HDFC_May.csv"),
        ("2026-05-14", "CULT FIT MEMBERSHIP", "CULT FIT MEMBERSHIP", "Subscriptions", 1499.0, "HDFC_May.csv"),
        ("2026-05-15", "AMAZON PAY INDIA", "AMAZON PAY INDIA", "Shopping", 4100.0, "HDFC_May.csv"),
        ("2026-05-17", "OLA CABS", "OLA CABS", "Transportation", 255.0, "HDFC_May.csv"),
        ("2026-05-19", "RELIANCE FRESH", "RELIANCE FRESH", "Groceries", 1120.0, "HDFC_May.csv"),
        ("2026-05-21", "ZOMATO ORDER", "ZOMATO ORDER", "Food & Dining", 480.0, "HDFC_May.csv"),
        ("2026-05-23", "SWIGGY BANGALORE", "SWIGGY BANGALORE", "Food & Dining", 395.0, "HDFC_May.csv"),
        ("2026-05-25", "AIRTEL BROADBAND", "AIRTEL BROADBAND", "Utilities", 999.0, "HDFC_May.csv"),
        ("2026-05-27", "DECATHLON SPORTS", "DECATHLON SPORTS", "Shopping", 2200.0, "HDFC_May.csv"),

        # June 2026 (ICICI_June.csv)
        ("2026-06-01", "AMAZON PAY INDIA", "AMAZON PAY INDIA", "Shopping", 2500.0, "ICICI_June.csv"),
        ("2026-06-03", "SWIGGY BANGALORE", "SWIGGY BANGALORE", "Food & Dining", 450.0, "ICICI_June.csv"),
        ("2026-06-04", "UBER TRIP", "UBER TRIP", "Transportation", 320.0, "ICICI_June.csv"),
        ("2026-06-05", "RELIANCE FRESH", "RELIANCE FRESH", "Groceries", 1200.0, "ICICI_June.csv"),
        ("2026-06-07", "NETFLIX SUBSCRIPTION", "NETFLIX SUBSCRIPTION", "Subscriptions", 499.0, "ICICI_June.csv"),
        ("2026-06-10", "SPOTIFY PREMIUM", "SPOTIFY PREMIUM", "Subscriptions", 119.0, "ICICI_June.csv"),
        ("2026-06-12", "ZOMATO ORDER", "ZOMATO ORDER", "Food & Dining", 610.0, "ICICI_June.csv"),
        ("2026-06-15", "BIGBASKET GROCERY", "BIGBASKET GROCERY", "Groceries", 2100.0, "ICICI_June.csv"),
        ("2026-06-18", "OLA CABS", "OLA CABS", "Transportation", 275.0, "ICICI_June.csv"),
        ("2026-06-20", "AMAZON PAY INDIA", "AMAZON PAY INDIA", "Shopping", 1800.0, "ICICI_June.csv"),
        ("2026-06-22", "CULT FIT MEMBERSHIP", "CULT FIT MEMBERSHIP", "Subscriptions", 1499.0, "ICICI_June.csv"),
        ("2026-06-25", "ELECTRICITY BOARD", "ELECTRICITY BOARD", "Utilities", 1450.0, "ICICI_June.csv"),
        ("2026-06-27", "RENT PAYMENT LANDLORD", "RENT PAYMENT LANDLORD", "Housing", 18000.0, "ICICI_June.csv")
    ]
    
    rows = [
        (date, extract_month(date), merchant, desc, cat, amt, src)
        for date, merchant, desc, cat, amt, src in transactions
    ]
    
    cursor.executemany(
        "INSERT INTO transactions (date, month, merchant, description, category, amount, source_file) VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows
    )
    
    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    print(f"Database seeded successfully at {DB_PATH} with {count} transactions.")
    conn.close()

if __name__ == "__main__":
    init_db()
