import sqlite3

def create_inventory():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS drugs (
            FIND INTEGER PRIMARY KEY NOT NULL,
            FNAME TEXT NOT NULL,
            AMOUNT INTEGER NOT NULL
        )
    ''')

    c.execute("INSERT INTO drugs (FIND, FNAME, AMOUNT) VALUES (1, 'Tylenol', 800)")
    c.execute("INSERT INTO drugs (FIND, FNAME, AMOUNT) VALUES (2, 'Advil', 100)")
    c.execute("INSERT INTO drugs (FIND, FNAME, AMOUNT) VALUES (3, 'random_drug', 1000)")

    conn.commit()
    print("yass queen")
    conn.close()

def pull_from_location(database, table):
    conn = sqlite3.connect(f'{database}.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table}")

    rows = c.fetchall()

    print("Table below\n")
    for row in rows:
        print(f"{row[0]}: {row[1]} {row[2]}")

    c.close()

def create_people():
    conn = sqlite3.connect('dave.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recommended (
            HOUR TEXT NOT NULL,
            NUMBER_TAKEN INTEGER NOT NULL,
            DRUG TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS taken (
            HOUR TEXT NOT NULL,
            NUMBER_TAKEN INTEGER NOT NULL,
            DRUG TEXT NOT NULL
            )
    ''')

    # c.execute("INSERT INTO recommended (HOUR, NUMBER_TAKEN, DRUG) VALUES ('06:00', 2, 'advil')")
    # c.execute("INSERT INTO recommended (HOUR, NUMBER_TAKEN, DRUG) VALUES ('08:00', 1, 'placeholder')")
    # c.execute("INSERT INTO recommended (HOUR, NUMBER_TAKEN, DRUG) VALUES ('18:00', 0, 'placeholder2')")
    # c.execute("INSERT INTO recommended (HOUR, NUMBER_TAKEN, DRUG) VALUES ('22:00', 0, 'placeholder3')")

    conn.commit()
    print("yass queen")
    conn.close()

def add_access(person, hour, drug, number):
    conn = sqlite3.connect(f'{person}.db')
    c = conn.cursor()
    
    c.execute(f"INSERT INTO taken (HOUR, NUMBER_TAKEN, DRUG) VALUES ({hour}, {number}, {drug})")
    conn.commit()
    conn.close()

add_access('dave','00:00','tylenol',1209843102943)
pull_from_location('dave','recommended')
pull_from_location('dave','taken')