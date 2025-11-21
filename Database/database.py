import sqlite3
import datetime

"""
Python file to access databases for project, functions can access different databases, such as the inventory database and the personal databases for all people 
"""

time_format = "%Y-%m-%d %H:%M:%S"

class DatabaseManager:
    def __init__(self, path_to_db):
        self.db_path = path_to_db
        self.create_inventory()


    def create_inventory(self):
        """
        This function just creates the inventory database, realistically it doesn't ever need to be used if the database is already created, will likely be deleted eventually, but keeping just in case for now

        It initializes the two tables for what we have and what drugs are possible, so you can pull based on barcodes.
        """
        conn = sqlite3.connect(self.db_path)
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

        c.execute('''
            CREATE TABLE IF NOT EXISTS drug_changes (
                barcode TEXT NOT NULL,
                dname TEXT NOT NULL,
                change INTEGER NOT NULL,
                user TEXT NOT NULL,
                type TEXT NOT NULL,
                time DATETIME NOT NULL,
                reason TEXT
                )
        ''')

        conn.commit()
        conn.close()


    def add_to_inventory(self, barcode, user):
        """
        Adds a drug to the inventory if it exists in the drugs database and logs the change.

        Parameters:
            barcode (str): The barcode of the drug to add.
            user (str): The user performing the addition.

        Returns:
            LookupError: If no drug is found with the given barcode.
            IndexError: If the drug is already in the inventory (integrity error).
            Exception: Any other exception encountered during insertion.
            None: On successful addition.

        Note:
            This method does not raise exceptions; instead, it returns exception types or instances on error.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM drugs WHERE barcode = ?", (barcode,))
        drug = c.fetchone()

        if not drug:
            print("No drug found with that barcode in database")
            conn.close()
            return LookupError

        try:
            c.execute('''
                INSERT INTO drugs_in_inventory (barcode, dname, estimated_amount, expiration_date)
                VALUES (?, ?, ?, ?)
            ''', (drug[0], drug[1], drug[2], drug[3]))
        except (sqlite3.IntegrityError):
            conn.close()
            return IndexError
        except Exception as e:
            conn.close()
            return e

        c.execute("INSERT INTO drug_changes (barcode, dname, change, user, type, time) VALUES (?,?,?,?,?,?)",(barcode, drug[1], drug[2], user, 'New Entry', datetime.datetime.now().strftime(time_format)))

        conn.commit()
        conn.close()


    def add_to_drugs_database(self, barcode, dname, amount, expiration_date):
        """
        Add a new drug to the drugs reference table.

        Parameters:
            barcode (str): The barcode of the drug.
            dname (str): The name of the drug.
            amount (int): The amount of the drug.
            expiration_date (date): The expiration date of the drug.

        Side effects:
            Inserts a new drug into the drugs table in the database.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("INSERT INTO drugs (barcode, dname, amount, expiration_date) VALUES (?,?,?,?)", (barcode, dname, amount, expiration_date))

        conn.commit()
        conn.close()


    def log_access_to_inventory(self, barcode, change, user):
        """
        Log changes to drug inventory amounts.

        Parameters:
            barcode (str): The barcode of the drug whose inventory is being updated.
            change (int): The amount to change the inventory by (positive or negative).
            user (str): The user making the change.

        Side effects:
            Updates the estimated amount of the drug in the inventory and logs the change in the drug_changes table.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM drugs_in_inventory WHERE barcode = ?", (barcode,))
        drug_info = c.fetchone()
        
        try:
            c.execute("UPDATE drugs_in_inventory SET estimated_amount = ? WHERE barcode = ?", (drug_info[2] + change, barcode))
            c.execute("INSERT INTO drug_changes (barcode, dname, change, type, user, time) VALUES (?,?,?,?,?)", (drug_info[0], drug_info[1], change, user, 'access', datetime.datetime.now().strftime(time_format)))
        except Exception as e:
            print("Error:",e)
        
        conn.commit()
        conn.close()


    def delete_entry(self, barcode, reason):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM drugs_in_inventory WHERE barcode = ?", (barcode,))
        drug_info = c.fetchone()

        c.execute("DELETE FROM drugs_in_inventory WHERE barcode = ?", (barcode,))

        c.execute("INSERT INTO drug_changes (barcode, dname, change, user, type, time, reason) VALUES (?,?,?,?,?,?,?)",(barcode, drug_info[1], drug_info[2], 'Admin', 'Delete Entry', datetime.datetime.now().strftime(time_format), reason,))

        conn.commit()
        conn.close()
        

    def pull_data(self, table):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(f"SELECT * FROM {table}")
        table = c.fetchall()
        
        conn.close()
        return table


class PersonalDatabaseManager:
    def __init__(self, path_to_database):
        self.db_path = path_to_database
        self.create_personal_database()

    def create_personal_database(self):
        """
        This function just creates the changes database, realistically it doesn't ever need to be used if the database is already created, will likely be deleted eventually, but keeping just in case for now
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS prescription(
                time TIME PRIMARY KEY NOT NULL,
                barcode TEXT NOT NULL,
                dname TEXT NOT NULL,
                number TEXT NOT NULL
                )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS history(
                time TIME PRIMARY KEY NOT NULL,
                barcode TEXT NOT NULL,
                dname TEXT NOT NULL,
                number TEXT NOT NULL)
        ''')

        conn.commit()
        conn.close()
    
    def add_prescription_med(self, time, barcode, number):
        pass

