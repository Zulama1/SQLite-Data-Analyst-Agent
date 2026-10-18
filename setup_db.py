import sqlite3
import pandas as pd

def init_database(excel_path:str = "ecommerce_testing_dataset.xlsx", db_path: str="database.db"):
    conn = sqlite3.connect(db_path)
    customers_df = pd.read_excel(excel_path, sheet_name="Customers")
    orders_df = pd.read_excel(excel_path, sheet_name="Orders")

    customers_df.to_sql("customers", conn, if_exists="replace", index=False)
    orders_df.to_sql("orders", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()
    print(f"Database {db_path} initialized with Customers and Order tables")

if __name__== "__main__":
    init_database()