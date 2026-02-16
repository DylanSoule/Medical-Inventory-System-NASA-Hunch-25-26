import mysql.connector
import csv


conn = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="1234",
    database="inventory_system"
)

c = conn.cursor()

tables = ('medications','in_inventory','people','prescriptions','assigned_prescriptions','history')

for table in tables:
    with open(f'database_setup/seeder_csvs/{table}.csv', 'r') as file:
        csvreader = csv.reader(file)
        for row in csvreader:
            c.execute(f"INSERT INTO {table} VALUES {tuple(row)};")



conn.commit()
conn.close()