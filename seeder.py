import sqlite3
import mysql.connector

liteconn = sqlite3.connect('Database/inventory.db')

myconn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="inventory_system"
)

lite_c = liteconn.cursor()

my_c = myconn.cursor()

lite_c.execute("SELECT barcode,estimated_amount FROM drugs_in_inventory;")
drugs = lite_c.fetchall()

for entry in drugs:
    my_c.execute("INSERT INTO in_inventory (barcode, amount) VALUES (%s, %s)", (entry[0],entry[1]))

liteconn.close()

myconn.commit()
myconn.close()