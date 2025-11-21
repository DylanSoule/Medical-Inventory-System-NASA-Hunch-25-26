import sqlite3
import datetime


def create_person(name):
    conn = sqlite3.connect(f'name.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS prescriptions (
            time TIME NOT NULL,
            num_taken INTEGER NOT NULL,
            barcode TEXT NOT NULL,
            dname TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS taken (
            time TIME NOT NULL,
            num_taken INTEGER NOT NULL,
            barcode TEXT NOT NULL,
            dname TEXT NOT NULL
            )
    ''')

    conn.commit()
    conn.close()

def add_access(person):
    conn = sqlite3.connect(f'{person}.db')
    c = conn.cursor()
    
    c.execute("INSERT INTO taken (HOUR, NUMBER_TAKEN, DRUG) VALUES (?, ?, ?)", (hour, number, drug))
    conn.commit()
    conn.close()
