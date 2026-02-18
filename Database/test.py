import sqlite3
from datetime import datetime, timedelta

time_format = "%Y-%m-%d %H:%M:%S"

conn = sqlite3.connect('Database/inventory.db')
c = conn.cursor()
today = datetime.today()

stop_date = (today - timedelta(days=31)).strftime(time_format)
c.execute("SELECT * FROM drug_changes WHERE time > ?", (stop_date,))
lis1t = c.fetchall()
conn.close()
print(lis1t)