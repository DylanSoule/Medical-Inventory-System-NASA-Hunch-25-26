import sqlite3
import mysql.connector

liteconn = sqlite3.connect('Database/inventory.db')

myconn = connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="inventory-system"
)

lite_c = liteconn.cursor()

my_c = myconn.cursor()

lite_c.execute("SELECT * FROM drugs;")
drugs = lite_c.fetchall()

for entry in drugs:
    my_c.execute("INSERT * INTO medications VALUES (?,?,?,?,?,?)",(entry[0],entry[1],entry[2],entry[4],entry[6]+' '+entry[5],entry[3]))

liteconn.close()
myconn.commit()
myconn.close()