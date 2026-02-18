import mysql.connector
from datetime import datetime, timedelta
import numpy as np


"""
Python file to access databases for project, functions can access different databases, such as the inventory database and the personal databases for all people
"""


time_format = "%Y-%m-%d %H:%M:%S"


class DatabaseManager:
    def __init__(self,user,password,database):
        self.user = user
        self.password = password
        self.database = database
        # self.create_inventory()

    """
    def create_inventory(self):
         
        This function just creates the inventory database, realistically it doesn't ever need to be used if the database is already created, will likely be deleted eventually, but keeping just in case for now

        It initializes the two tables for what we have and what drugs are possible, so you can pull based on barcodes.
        
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
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
    """

    def add_to_inventory(self, barcode, user,location):
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
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()

        c.execute("SELECT barcode, amount_in_unit FROM medications WHERE barcode = %s", (barcode,))
        drug = c.fetchone()

        if not drug:
            print("No drug found with that barcode in database")
            conn.close()
            return LookupError

        try:
            c.execute('''
                INSERT INTO in_inventory (barcode, estimated_amount_remaining, location)
                VALUES (%s, %s, %s)
            ''', (drug[0], drug[1],location,))
        except (mysql.IntegrityError):
            conn.close()
            return IndexError
        except Exception as e:
            conn.close()
            return e

        c.execute("SELECT MAX(id) FROM in_inventory;")
        iid = c.fetchone[0]
        c.execute("SELECT id FROM people WHERE name = %s",(user,))
        pid = c.fetchone[0]
        c.execute("INSERT INTO history (barcode, inventory_id, person_id, type_of_use, time_of_use) VALUES (%s,%s,%s,%s,%s)",(barcode, iid, pid, 'New Entry', datetime.now().strftime(time_format),)) 

        conn.commit()
        conn.close()



    def add_to_drugs_database(self, barcode, name, amount, Type, item_type, dose_size, expiration_date):
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
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()
        
        c.execute("INSERT INTO medications (barcode, name, amount_in_unit, type, dosage,expiration_date) VALUES (%s,%s,%s,%s,%s)", (barcode, name, amount,Type,item_type + ' ' + dose_size,expiration_date))

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
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()


        c.execute("SELECT id, estimated_amount_remaining FROM in_inventory WHERE barcode = %s", (barcode,))
        drug_info = c.fetchone()
        
        try:
            c.execute("UPDATE drugs_in_inventory SET estimated_amount = %s WHERE barcode = %s", (drug_info[1] + change, barcode))
            c.execute("INSERT INTO history (barcode, inventory_id, person_id, type_of_use, time_of_use, change) VALUES (%s,%s,%s,%s,%s)", (barcode, drug_info[0], change, user, 'Access', datetime.now().strftime(time_format),change))
        except Exception as e:
            print("Error:",e)
        
        conn.commit()
        conn.close()
  

    def check_if_barcode_exists(self, barcode):
        """
        Check if a barcode is in the inventory
        
        :param self: class path to inventory
        :param barcode: barcode being checked
        """
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()

        c.execute("SELECT medications.name AS name FROM medications JOIN in_inventory ON medications.barcode=in_inventory.barcode WHERE in_inventory.barcode=%s", (barcode,))
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
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()

        c.execute("SELECT id FROM in_inventory WHERE barcode = %s", (barcode,))
        iid = c.fetchone()[0]

        c.execute("SELECT id FROM people WHERE name=%s",('admin',))
        pid= c.fetchone()[0]

        c.execute("DELETE FROM drugs_in_inventory WHERE barcode = %s", (barcode,))

        c.execute("INSERT INTO drug_changes (barcode, inventory_id, person_id, type_of_use, time_of_use, reason) VALUES (%s,%s,%s,%s,%s,%s)",(barcode, iid, pid, 'Delete Entry', datetime.now().strftime(time_format), reason,))

        conn.commit()
        conn.close()
    

    def pattern_recognition(
        self,
        periods=[4,7,14,30],
        periods_back=5,
        users=['dylan'],
        whole=True,
        z_thresh=2.0,
        ratio_thresh=1.2,
        baseline_window=3
    ):
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
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
                        FROM history
                        WHERE time_of_use BETWEEN %s AND %s
                    """, (back, front))

                    totals.append(c.fetchone()[0])

                results.extend(
                    analyze_series(totals, f"whole_{period}d")
                )

        # ---- PER USER ----
        if users:
            for user in users:
                c.execute("SELECT id FROM people WHERE name=%s",(user,))
                pid=c.fetchall()[0]
                for period in periods:
                    totals = []
                    for i in range(periods_back):
                        front = (today - timedelta(days=i*period)).strftime(time_format)
                        back = (today - timedelta(days=(i+1)*period)).strftime(time_format)

                        c.execute("""
                            SELECT COALESCE(SUM(change), 0)
                            FROM history
                            WHERE time_of_use BETWEEN %s
                            AND %s
                            AND person_id = %s
                        """, (back, front, pid))

                        totals.append(c.fetchone()[0])

                    results.extend(
                        analyze_series(totals, f"user:{user}_{period}d")
                    )

        conn.close()
        return results

    
    def give_inventory_data(self): #for later, just transitioning to not change frontend right now
        pass
        # conn = mysql.connector.connect(
        #     host="127.0.0.1",
        #     port=3306,
        #     user=self.user,
        #     password=self.password,
        #     database=self.database
        # )
        # c = conn.cursor()

        # c.execute("SELECT ")

    def give_history_data(self): #for later, just transitioning to not change frontend right now
        pass



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
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()

        if table=="in_inventory":
            c.execute("""SELECT medications.name, in_inventory.barcode, in_inventory.estimated_amount_remaining, medications.expiration_date,medications.type,medications.dosage 
                      FROM in_inventory
                      JOIN medications ON medications.barcode=in_inventory.barcode;""")
            table=c.fetchall()
            new = table[5].split()
            table[5]=new[0]+new[1]
            table.append(new[2])
        elif table =="history":
            c.execute("""SELECT history.barcode, medications.name,history.change,people.name,history.type_of_use,history.time_of_use,history.reason FROM history
                      JOIN medications ON medications.barcode=history.barcode
                      JOIN people ON people.id=history.person_id
                      WHERE history.time_of_use >= %s and history.time_of_use <= %s
                      ORDER BY history.time_of_use DESC;""", (datetime.now() + timedelta(-7)).strftime(time_format),(datetime.now()+timedelta(1)).strftime(time_format),)
            table=c.fetchall()
        else:
            c.execute(f"SELECT * FROM {table}")
            table = c.fetchall()
        
        conn.close()
        return table


class PersonalDatabaseManager:
    def __init__(self,user,password,database,access_user):
        self.user = user
        self.password = password
        self.database = database
        self.access_user = access_user
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()
        c.execute("SELECT id FROM people WHERE name=%s",(access_user,))
        self.user_id=c.fetchone[0]
        conn.close()
        #create_personal_database()

    """
    def create_personal_database(self):
        ""
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
        ""
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
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
    """
        
    def add_prescription_med(self, barcode, dose, frequency=None, leeway=None, time=None, drug_name=None, as_needed=True):
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()


        c.execute("INSERT INTO prescriptions (barcode, dose, time, frequency, time, leeway, as_needed) VALUES (%s,%s,%s,%s,%s,%s,%s)", (barcode, dose, time, frequency, leeway, as_needed))
        c.execute("INSERT INTO assigned_prescriptions (person_id,prescription_id) VALUES (%s, (SELECT MAX(id) FROM prescriptions));",(self.user_id))


        conn.commit()
        conn.close()


    def compare_history_with_prescription(self, days_back=7):
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()

        deadline = (datetime.today() + timedelta(days=(days_back*-1))).strftime(time_format)


        c.execute("SELECT barcode,time_of_use FROM history WHERE when_taken > %s AND person_id=%s", (deadline,self.user_id,))
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
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()

        c.execute("SELECT barcode,time_of_use FROM history WHERE person_id = %s ORDER BY id DESC LIMIT 1",(self.user_id,))
        last_taken = c.fetchone()
        print(last_taken)
        result = self.compare_with_prescription(last_taken)
        
        conn.close()
        return(result)
    
    def compare_with_prescription(self, log):
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()
        
        c.execute("SELECT assigned_prescriptions FROM assigned_prescriptions WHERE barcode = %s",(log[0]))
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
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()
        
        print(self.db_path)

        c.execute('SELECT * FROM history WHERE when_taken = %s',(date,))
        hist_logs = c.fetchall()

        c.execute('SELECT barcode, dname, dosage, frequency, time, leeway, start_date FROM prescription WHERE as_needed = %s', (False,))
        prescript_dates = c.fetchall()
        prescript_logs= []
        for prescript in prescript_dates:
            pdate = datetime.strptime(prescript[6], time_format)
            pdate = pdate.date()
            ndate = datetime.strptime(date, time_format)
            ndate = ndate.date()

            diff = (pdate-ndate).total_seconds()

            if (diff/86400)%prescript[3]==0:
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
    #     conn = mysql.connector.connect(
        #     host="127.0.0.1",
        #     port=3306,
        #     user=self.user,
        #     password=self.password,
        #     database=self.database
        # )
    #     c = conn.cursor()


   #     c.execute("INSERT INTO history (barcode, dname, when_taken, dose) VALUES (%s,%s,%s,%s)", (barcode, drug_name, datetime.now().strftime(time_format), dose))


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
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=self.user,
            password=self.password,
            database=self.database
        )
        c = conn.cursor()


        c.execute(f"SELECT * FROM {table}")
        table = c.fetchall()
        
        conn.close()
        return table
  


if __name__ == "__main__":
    read = PersonalDatabaseManager('Database/dylan_records.db')
    read1 = DatabaseManager('Database/inventory.db')

    print(read1.pattern_recognition())
    # print(read.pull_data('history'))
    # print(read.compare_history_with_prescription(days_back=60))
    # print(read.compare_most_recent_log_with_prescription())


    # print(str(read.pull_data('prescription')).replace('),',')\n'))


    # UPDATE table_name SET column_name = new_value WHERE condition
