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
                barcode TEXT PRIMARY KEY NOT NULL UNIQUE,
                dname TEXT NOT NULL,
                estimated_amount INTEGER NOT NULL,
                expiration_date DATE NOT NULL,
                type TEXT NOT NULL,
                item_type TEXT NOT NULL,
                dose_size TEXT NOT NULL
            )
        ''')


        c.execute('''
            CREATE TABLE IF NOT EXISTS drugs(
                barcode TEXT PRIMARY KEY NOT NULL UNIQUE,
                dname TEXT NOT NULL,
                amount INTEGER NOT NULL,
                expiration_date DATE NOT NULL,
                type TEXT NOT NULL,
                item_type TEXT NOT NULL,
                dose_size TEXT NOT NULL
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




    def add_to_drugs_database(self, barcode, dname, amount, expiration_date, Type, item_type, dose_size):
        """
        Add a new drug to the drugs reference table.


        Parameters:
            barcode (str): The barcode of the drug.
            dname (str): The name of the drug.
            amount (int): The amount of the drug.
            expiration_date (date): The expiration date of the drug.
            type (str): the type of the drug(Antibiotic, Antihistamine, etc.)
            item_type(str): the method the drug is taken(Pill, Eye Drop, Ointment, etc.)
            dose_size(str): The dose size of the drug


        Effects:
            Inserts a new drug into the drugs table in the database.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("INSERT INTO drugs (barcode, dname, amount, expiration_date, type, item_type, dose_size) VALUES (?,?,?,?,?,?,?)", (barcode, dname, amount, expiration_date,Type,item_type, dose_size))


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
            c.execute("INSERT INTO drug_changes (barcode, dname, change, user, type, time) VALUES (?,?,?,?,?,?)", (drug_info[0], drug_info[1], change, user, 'Access', datetime.datetime.now().strftime(time_format)))
        except Exception as e:
            print("Error:",e)
        
        conn.commit()
        conn.close()


        conn = sqlite3.connect(f'Database/{user.lower()}_records.db')
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO history (barcode, dname, when_taken, dose) VALUES (?,?,?,?)", (drug_info[0], drug_info[1], datetime.datetime.now().strftime(time_format), abs(change)))
        except Exception as e:
            print("Error:",e)

        conn.commit()
        conn.close()

    

    def log_access_to_inventory_with_mutable_date(self, barcode, change, user, date_time): # FOR TESTING ONLY
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
            c.execute("INSERT INTO drug_changes (barcode, dname, change, user, type, time) VALUES (?,?,?,?,?,?)", (drug_info[0], drug_info[1], change, user, 'Access', date_time))
        except Exception as e:
            print("Error:",e)
        
        conn.commit()
        conn.close()


        conn = sqlite3.connect(f'Database/{user.lower()}_records.db')
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO history (barcode, dname, when_taken, dose) VALUES (?,?,?,?)", (drug_info[0], drug_info[1], date_time, abs(change)))
        except Exception as e:
            print("Error:",e)

        conn.commit()
        conn.close()

  
    def delete_entry(self, barcode, reason):
        """
        Deletes an entry from the inventory and logs the deletion in the drug_changes history.


        Parameters:
            barcode (str): The barcode of the drug to delete from inventory.
            reason (str): The reason for deleting the entry.


        Side effects:
            Removes the entry from the drugs_in_inventory table and adds a record to the drug_changes table.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()


        c.execute("SELECT * FROM drugs_in_inventory WHERE barcode = ?", (barcode,))
        drug_info = c.fetchone()


        c.execute("DELETE FROM drugs_in_inventory WHERE barcode = ?", (barcode,))


        c.execute("INSERT INTO drug_changes (barcode, dname, change, user, type, time, reason) VALUES (?,?,?,?,?,?,?)",(barcode, drug_info[1], drug_info[2], 'Admin', 'Delete Entry', datetime.datetime.now().strftime(time_format), reason,))


        conn.commit()
        conn.close()
      


    def pull_data(self, table):
        """
        Retrieve all records from a specified table in the database.


        Parameters:
            table (str): Name of the table to query.


        Returns:
            list of tuples: Each tuple contains the records from the specified table.


        Security Considerations:
            The table name is interpolated directly into the SQL query, which can lead to SQL injection
            if the table name is not properly validated. Ensure that the table name is validated against
            a whitelist of expected table names before calling this function.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()


        c.execute(f"SELECT * FROM {table}")
        table = c.fetchall()
        
        conn.close()
        return table




class PersonalDatabaseManager:
    def __init__(self, path_to_person_database):
        self.db_path = path_to_person_database
        self.create_personal_database()


    def create_personal_database(self):
        """
        This function just creates the changes database, and checks that it exists every time the class is called


        prescription table:
            barcode - same as in inventory db, and is used as identifier
            dname - name of drug
            dosage - their dose for the prescription in number of eg. pills, or a normal dose
            frequency - how often they take the drug in days(eg. 1 means every day, 2 is every other day, 4 is every 4 days, and 7 is weekly)
            time - if they have one, when they should take the medication(Not needed for database)(in HH:MM:SS)
            leeway - how long they have before or after to take the drug before alert is raised(in minutes)
            start_date - when they first started taking the medication, or a day that they were supposed to take it, used to calculate when they should take it in the future(in %Y-%m-%d)
            end_date - when they stop taking their prescription(Not needed for database to work)
        
        history table:
            barcode - same as in inventory db, and is used as identifier
            dname - name of drug
            when_taken - when they took the medication, used to compare with prescriptions
            dose - how big of a dose they take, used to compare with prescriptions
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS prescription(
                barcode TEXT NOT NULL,
                dname TEXT NOT NULL,
                dosage INTEGER NOT NULL,
                frequency INTEGER,
                time TIME,
                leeway INTEGER,
                start_date DATE,
                end_date DATE,
                as_needed BOOLEAN
            )
        ''')


        c.execute('''
            CREATE TABLE IF NOT EXISTS history(
                barcode TEXT,
                dname TEXT NOT NULL,
                when_taken DATETIME NOT NULL,
                dose TEXT NOT NULL
            )
        ''')


        conn.commit()
        conn.close()
  
    def add_prescription_med(self, barcode, dose, frequency, start_date, leeway=None, end_date=None, time=None, drug_name=None, as_needed=False):
        if drug_name == None:
            conn = sqlite3.connect('Database/inventory.db')
            cur = conn.cursor()
            cur.execute(f"SELECT dname FROM drugs WHERE barcode = {barcode}")
            drug_name = cur.fetchone()[0]
            conn.close()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()


        c.execute("INSERT INTO prescription (barcode, dname, dosage, frequency, time, leeway, start_date, end_date, as_needed) VALUES (?,?,?,?,?,?,?,?,?)", (barcode, drug_name, dose, frequency, time, leeway, start_date, end_date, as_needed))


        conn.commit()
        conn.close()

    def compare_history_with_prescription(days_back):
        pass

    def compare_log_with_prescription(row):
        pass

    '''The following is an old function that is not in use but being kept around just in case'''
    # def log_access(self, barcode, dose, drug_name=None):
    #     if drug_name == None:
    #         conn = sqlite3.connect('Database/inventory.db')
    #         cur = conn.cursor()
    #         cur.execute(f"SELECT dname FROM drugs WHERE barcode = {barcode}")
    #         drug_name = cur.fetchone()[0]
    #         conn.close()
    #     conn = sqlite3.connect(self.db_path)
    #     c = conn.cursor()


   #     c.execute("INSERT INTO history (barcode, dname, when_taken, dose) VALUES (?,?,?,?)", (barcode, drug_name, datetime.datetime.now().strftime(time_format), dose))


   #     conn.commit()
   #     conn.close()


    def pull_data(self, table):
        """
        Retrieve all records from a specified table in the database.


        Parameters:
            table (str): Name of the table to query.


        Returns:
            list of tuples: Each tuple contains the records from the specified table.


        Security Considerations:
            The table name is interpolated directly into the SQL query, which can lead to SQL injection
            if the table name is not properly validated. Ensure that the table name is validated against
            a whitelist of expected table names before calling this function.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()


        c.execute(f"SELECT * FROM {table}")
        table = c.fetchall()
        
        conn.close()
        return table
  


if __name__ == "__main__":
    read = PersonalDatabaseManager('Database/dylan_records.db')
    read1 = DatabaseManager('Database/inventory.db')

   
    #  def log_access_to_inventory_with_mutable_date(self, barcode, change, user, date_time): # FOR TESTING ONLY

    # print(str(read1.pull_data('drug_changes')).replace('),',')\n'))
    # print(str(read.pull_data('prescription')).replace('),',')\n'))


    # time_format = "%Y-%m-%d %H:%M:%S"

