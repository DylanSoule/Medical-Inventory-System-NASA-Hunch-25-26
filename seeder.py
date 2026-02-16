import sqlite3
import mysql.connector

liteconn = sqlite3.connect('Database/inventory.db')

myconn = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="1234",
    database="inventory_system"
)

lite_c = liteconn.cursor()

my_c = myconn.cursor()

lite_c.execute("SELECT barcode,estimated_amount FROM drugs;")
drugs = lite_c.fetchall()

for entry in drugs:
    my_c.execute("INSERT INTO medications (barcode, name, amount_in_unit, type, dosage) VALUES (%s, %s,%s,%s,%s)", (entry[0],entry[1], entry[2],entry[4],entry[5]+entry[6]))

liteconn.close()

myconn.commit()
myconn.close()