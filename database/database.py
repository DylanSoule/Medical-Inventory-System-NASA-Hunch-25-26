import sqlite3
import datetime

"""
Python file to access databases for project, functions can access different databases, such as the inventory database and the personal databases for all people 
"""

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.replace(tzinfo=None).isoformat()

def create_explicit_inventory():
    """
    This function just creates the inventory database, realistically it doesn't ever need to be used if the database is already created, will likely be deleted eventually, but keeping just in case for now

    It initializes the two tables for what we have and what drugs are possible, so you can pull based on barcodes.
    """
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS drugs_in_inventory (
            barcode TEXT PRIMARY KEY NOT NULL,
            dname TEXT NOT NULL,
            estimated_amount INTEGER NOT NULL,
            expiration_date DATE NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS drugs(
            barcode TEXT PRIMARY KEY NOT NULL,
            dname TEXT NOT NULL,
            amount INTEGER NOT NULL,
            expiration_date DATE NOT NULL      
        )
    ''')

    c.execute("INSERT INTO drugs (barcode, dname, amount, expiration_date) VALUES ('124N3XY', 'Tylenol', 200, '2025-12-25')")
    c.execute("INSERT INTO drugs (barcode, dname, amount, expiration_date) VALUES ('1NP3XY', 'Drug', 200, '2025-11-25')")
    c.execute("INSERT INTO drugs (barcode, dname, amount, expiration_date) VALUES ('98Z64N3XY', 'Coke', 200, '2025-11-22')")

    conn.commit()
    conn.close()


def create_changes_database():
    """
    This function just creates the changes database, realistically it doesn't ever need to be used if the database is already created, will likely be deleted eventually, but keeping just in case for now
    """
    conn = sqlite3.connect('changes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS drug_changes (
            barcode TEXT NOT NULL,
            dname TEXT NOT NULL,
            change INTEGER NOT NULL,
            time DATETIME NOT NULL
            )
    ''')

    conn.commit()
    conn.close()


def add_to_inventory_via_barcode(barcode):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()

    c.execute("SELECT * FROM drugs WHERE barcode = ?", (barcode,))
    drug = c.fetchone()

    if not drug:
        print("No drug found with that barcode in database")
        conn.close()
        return

    try:
        c.execute('''
            INSERT INTO drugs_in_inventory (barcode, dname, estimated_amount, expiration_date)
            VALUES (?, ?, ?, ?)
        ''', (drug[0], drug[1], drug[2], drug[3]))
    except (sqlite3.IntegrityError):
        print("Already drug in inventory with that barcode")
    except:
        print("Unknown failure")

    conn.commit()
    conn.close()


def add_to_drugs_database(barcode, dname, amount, expiration_date):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    c.execute("INSERT INTO drugs (barcode, dname, amount, expiration_date) VALUES (?,?,?,?)", (barcode, dname, amount, expiration_date))

    conn.commit()
    conn.close()


def log_access_to_inventory(barcode, change):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()

    change_conn = sqlite3.connect('changes.db')
    change_c = change_conn.cursor()

    c.execute("SELECT * FROM drugs_in_inventory WHERE barcode = ?", (barcode,))
    drug_info = c.fetchone()

    if not drug_info:
        print("No drug found with that barcode in database")
        conn.close()
        change_conn.close()
        return
    
    try:
        c.execute("UPDATE drugs_in_inventory SET estimated_amount = ? WHERE barcode = ?", (drug_info[2] + change, barcode))
        change_c.execute("INSERT INTO drug_changes (barcode, dname, change, time) VALUES (?,?,?,?)", (drug_info[0], drug_info[1], change, adapt_datetime_iso(datetime.datetime.now())))
    except Exception as e:
        print("Error:",e)
    
    conn.commit()
    change_conn.commit()
    conn.close()
    change_conn.close()


def pull_from_drug_inventory(database, table):
    conn = sqlite3.connect(f'{database}.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table}")

    rows = c.fetchall()

    print("Table below\n")
    for row in rows:
        print(f"Barcode: {row[0]} | Name: {row[1]} | Amount: {row[2]} | Expiration Date: {row[3]}")

    c.close()

def pull_table_from_database(database, table):
    conn = sqlite3.connect(f"{database}.db")
    c = conn.cursor()

    c.execute(f"SELECT * FROM {table}")
    table = c.fetchall()

    for row in table:
        print(row)



"""
Stuff below this is for people databases, and will be worked on in the future
Not right now, doing the drug databases at this point
"""
# def create_people():
#     conn = sqlite3.connect('dave.db')
#     c = conn.cursor()
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS recommended (
#             HOUR TEXT NOT NULL,
#             NUMBER_TAKEN INTEGER NOT NULL,
#             DRUG TEXT NOT NULL
#         )
#     ''')
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS taken (
#             HOUR TEXT NOT NULL,
#             NUMBER_TAKEN INTEGER NOT NULL,
#             DRUG TEXT NOT NULL
#             )
#     ''')

#     conn.commit()
#     print("yass queen")
#     conn.close()

# def add_access(person, hour, drug, number):
#     conn = sqlite3.connect(f'{person}.db')
#     c = conn.cursor()
    
#     c.execute(f"INSERT INTO taken (HOUR, NUMBER_TAKEN, DRUG) VALUES ({hour}, {number}, {drug})")
#     conn.commit()
#     conn.close()

