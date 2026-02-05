import sqlite3
from datetime import datetime, timedelta
import numpy as np


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
                INSERT INTO drugs_in_inventory (barcode, dname, estimated_amount, expiration_date, type, item_type, dose_size)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (drug[0], drug[1], drug[2], drug[3], drug[4], drug[5], drug[6]))
        except (sqlite3.IntegrityError):
            conn.close()
            return IndexError
        except Exception as e:
            conn.close()
            return e

        c.execute("INSERT INTO drug_changes (barcode, dname, change, user, type, time) VALUES (?,?,?,?,?,?)",(barcode, drug[1], drug[2], user, 'New Entry', datetime.now().strftime(time_format)))

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

    

    def log_access_to_inventory_with_mutable_date(
        self,
        inventory_cursor,
        history_cursor,
        barcode,
        change,
        user,
        date_time
    ):  # FOR TESTING ONLY DELETE BEFORE FINAL PRODUCT
        """
        Log changes to drug inventory amounts using existing DB connections.
        """

        inventory_cursor.execute(
            "SELECT barcode, dname, estimated_amount FROM drugs_in_inventory WHERE barcode = ?",
            (barcode,)
        )
        drug_info = inventory_cursor.fetchone()

        if not drug_info:
            raise ValueError(f"Barcode {barcode} not found in inventory")

        try:
            inventory_cursor.execute(
                "UPDATE drugs_in_inventory SET estimated_amount = ? WHERE barcode = ?",
                (drug_info[2] + change, barcode)
            )

            inventory_cursor.execute(
                """
                INSERT INTO drug_changes (barcode, dname, change, user, type, time)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (drug_info[0], drug_info[1], change, user, 'Access', date_time)
            )

            history_cursor.execute(
                """
                INSERT INTO history (barcode, dname, when_taken, dose)
                VALUES (?, ?, ?, ?)
                """,
                (drug_info[0], drug_info[1], date_time, abs(change))
            )

        except Exception as e:
            print("Database error:", e)
            raise


  

    def check_if_barcode_exists(self, barcode):
        """
        Check if a barcode is in the inventory
        
        :param self: class path to inventory
        :param barcode: barcode being checked
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM drugs_in_inventory WHERE barcode = ?", (barcode,))
        check = c.fetchone()

        if not check:
            conn.close()
            return False
        conn.close()
        return True, check[1]


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

        c.execute("INSERT INTO drug_changes (barcode, dname, change, user, type, time, reason) VALUES (?,?,?,?,?,?,?)",(barcode, drug_info[1], drug_info[2], 'Admin', 'Delete Entry', datetime.now().strftime(time_format), reason,))

        conn.commit()
        conn.close()
    

    def pattern_recognition1(
        self,
        periods=[4,7,14,30],
        periods_back=5,
        users=['dylan'],
        whole=True,
        z_thresh=2.0,
        ratio_thresh=1.2,
        baseline_window=3
    ):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        today = datetime.today()

        results = []

        def analyze_series(values, label):
            anomalies = []
            values = np.array(values, dtype=float)

            for i in range(baseline_window, len(values)):
                baseline = values[i-baseline_window:i]
                mean = baseline.mean()
                std = baseline.std(ddof=1) or 1  # prevent divide-by-zero

                z = (values[i] - mean) / std
                ratio = values[i] / mean if mean > 0 else 0

                if abs(z) > z_thresh or ratio > ratio_thresh:
                    anomalies.append({
                        "label": label,
                        "index": i,
                        "value": values[i],
                        "baseline_mean": round(mean, 2),
                        "z_score": round(z, 2),
                        "ratio": round(ratio, 2),
                        "type": (
                            "spike" if values[i] > mean
                            else "drop"
                        )
                    })
            return anomalies

        # ---- WHOLE SYSTEM ----
        if whole:
            for period in periods:
                totals = []
                for i in range(periods_back):
                    front = (today - timedelta(days=i*period)).strftime(time_format)
                    back = (today - timedelta(days=(i+1)*period)).strftime(time_format)

                    c.execute("""
                        SELECT COALESCE(SUM(change), 0)
                        FROM drug_changes
                        WHERE time BETWEEN ? AND ?
                    """, (back, front))

                    totals.append(c.fetchone()[0])

                results.extend(
                    analyze_series(totals, f"whole_{period}d")
                )

        # ---- PER USER ----
        if users:
            for user in users:
                for period in periods:
                    totals = []
                    for i in range(periods_back):
                        front = (today - timedelta(days=i*period)).strftime(time_format)
                        back = (today - timedelta(days=(i+1)*period)).strftime(time_format)

                        c.execute("""
                            SELECT COALESCE(SUM(change), 0)
                            FROM drug_changes
                            WHERE time BETWEEN ?
                            AND ?
                            AND user = ?
                        """, (back, front, user))

                        totals.append(c.fetchone()[0])

                    results.extend(
                        analyze_series(totals, f"user:{user}_{period}d")
                    )

        conn.close()
        return results

    

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
            start_date - when they first started taking the medication, or a day that they were supposed to take it, used to calculate when they should take it in the future(in %Y-%m-%d %H:%M:%S)
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
                start_date DATETIME,
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


    def compare_history_with_prescription(self, days_back=7):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        deadline = (datetime.today() + timedelta(days=(days_back*-1))).strftime(time_format)


        c.execute("SELECT * FROM history WHERE when_taken > ?", (deadline,))
        history = c.fetchall()
        # print(history)
        flags = []

        for log in history:
            # print(log)
            result = self.compare_with_prescription(log)
            # print(result)
            flags.append((result[0], result[1], log[0], log[2]))

        return flags


    def compare_most_recent_log_with_prescription(self):
        """
        Docstring for compare_most_recent_log_with_prescription

        function compares most recent log by the person who's inventory is being accessed with their prescriptions
        
        :param self: pulls inventory path to personal database from class call

        return True or False based on if match is found or not
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM history ORDER BY rowid DESC LIMIT 1")
        last_taken = c.fetchone()
        print(last_taken)
        result = self.compare_with_prescription(last_taken)
        
        conn.close()
        return(result)
    
    def compare_with_prescription(self, log):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute(f"SELECT * FROM prescription WHERE barcode = {log[0]}")
        matching_prescriptions = c.fetchall()

        if matching_prescriptions == []:
            conn.close()
            return False, "No Matches Found"
        try:
            date_taken = datetime.strptime(log[2], time_format)
        except TypeError:
            for prescription in matching_prescriptions:
                if prescription[8] == True:
                    conn.close()
                    return True, "As needed"
            return False, "Datetime"

        for prescription in matching_prescriptions:
            prescription_start_date = datetime.strptime(prescription[6], time_format)
            difference = (date_taken - prescription_start_date).total_seconds()
            if (86400 - (difference % (prescription[3]*86400))) <= float(prescription[5] * 3600) or (difference % (prescription[3]*86400)) <= float(prescription[5] * 3600) and (int(log[3]) == prescription[2]):
                conn.close()
                return True, "Matches Prescription"
        conn.close()
        return False, "No Time Match"


    def get_personal_data(self, date):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('SELECT * FROM history WHERE when_taken = ?',(date,))
        hist_logs = c.fetchall()

        c.execute('SELECT barcode, dname, dosage, frequency, time, leeway, start_date FROM prescription WHERE as_needed = ?', (False,))
        prescript_dates = c.fetchall()
        prescript_logs= []
        for prescript in prescript_dates:
            pdate = datetime.strptime(prescript[6], time_format)
            pdate = pdate.date()
            ndate = datetime.strptime(date, time_format)
            ndate = ndate.date()

            diff = (pdate-ndate).total_seconds()

            if (diff/86400)%prescript[2]==0:
                prescript_logs.append((prescript[0],prescript[1],prescript[2], prescript[4], prescript[5],))
        
        return hist_logs, prescript_logs



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


   #     c.execute("INSERT INTO history (barcode, dname, when_taken, dose) VALUES (?,?,?,?)", (barcode, drug_name, datetime.now().strftime(time_format), dose))


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
    read1 = DatabaseManager('Database/inventory.db')

    import random

    # ===== CONFIG =====
    random.seed(42)

    start = datetime(2025, 9, 1)
    end = datetime(2026, 3, 15)

    # ===== OPEN CONNECTIONS ONCE =====
    inventory_conn = sqlite3.connect(read1.db_path)
    history_conn = sqlite3.connect("Database/brody_records.db")

    inventory_cursor = inventory_conn.cursor()
    history_cursor = history_conn.cursor()

    # Optional but recommended
    inventory_cursor.execute("PRAGMA journal_mode=WAL;")
    history_cursor.execute("PRAGMA journal_mode=WAL;")

    inventory_conn.execute("BEGIN TRANSACTION")
    history_conn.execute("BEGIN TRANSACTION")

    inventory_cursor.execute("SELECT barcode FROM drugs_in_inventory;")
    barcodes = inventory_cursor.fetchall()
    
    current = start

    while current <= end:
        date_str = current.strftime('%Y-%m-%d')


        barcode = random.choice(barcodes)

        time = random.choice(['05:00:00', '06:00:00','07:00:00','08:00:00','09:00:00','10:00:00','11:00:00','12:00:00','13:00:00','14:00:00','15:00:00','16:00:00','17:00:00','18:00:00','19:00:00'])
        read1.log_access_to_inventory_with_mutable_date(
            inventory_cursor,
            history_cursor,
            barcode[0],
            -2,
            'brody',
            f'{date_str} {time}'
        )



        # if random.random() > 0.35:
        #     caffeine_time = (
        #         random.choice(['09:15:00', '04:45:00'])
        #         if random.random() < 0.10
        #         else random.choice(['05:30:00', '06:00:00', '06:30:00','07:00:00', '07:30:00', '08:00:00'])
        #     )

        #     read1.log_access_to_inventory_with_mutable_date(
        #         inventory_cursor,
        #         history_cursor,
        #         '982136058275',
        #         -2,
        #         'lucca',
        #         f'{date_str} {caffeine_time}'
        #     )
    


        # # ===== IBUPROFEN (never fully skipped) =====
        # ibuprofen_doses = ['08:00:00', '14:00:00', '20:00:00']
        # skipped_dose = random.choice(ibuprofen_doses) if random.random() < 0.15 else None

        # for scheduled_time in ibuprofen_doses:
        #     if scheduled_time == skipped_dose:
        #         continue

        #     if random.random() < 0.10:
        #         time = {
        #             '08:00:00': random.choice(['07:10:00', '08:45:00']),
        #             '14:00:00': random.choice(['13:10:00', '14:45:00']),
        #             '20:00:00': random.choice(['19:10:00', '20:45:00']),
        #         }[scheduled_time]
        #     else:
        #         time = {
        #             '08:00:00': random.choice(['07:45:00', '08:00:00', '08:20:00']),
        #             '14:00:00': random.choice(['13:45:00', '14:00:00', '14:20:00']),
        #             '20:00:00': random.choice(['19:45:00', '20:00:00', '20:20:00']),
        #         }[scheduled_time]

        #     read1.log_access_to_inventory_with_mutable_date(
        #         inventory_cursor,
        #         history_cursor,
        #         '910348161816',
        #         -1,
        #         'dylan',
        #         f'{date_str} {time}'
        #     )

        current += timedelta(days=1)

    # ===== COMMIT ONCE =====
    inventory_conn.commit()
    history_conn.commit()

    inventory_conn.close()
    history_conn.close()


