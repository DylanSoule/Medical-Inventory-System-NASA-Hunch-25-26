import mysql.connector
import csv


conn = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="password",
    database="inventory_system"
)

c = conn.cursor()


with open('database_setup/seeder_csvs/medications.csv','r') as file:
    csvreader = csv.reader(file)
    next(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO medications (barcode, name, amount_in_unit,type,usage,expiration_date) VALUES (%s,%s,%s,%s,%s)",row[1::])
        except Exception as e:
            print(f"Error in table medications with row {row}")
            print(e)
            break

with open('database_setup/seeder_csvs/in_inventory.csv','r') as file:
    csvreader = csv.reader(file)

    next(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO in_inventory (barcode,estimated_amount_remaining,location) VALUES (%s,%s,%s)",(row[1],int(row[2]),row[4],))
        except Exception as e:
            print(f"Error in table in_inventory with row {row}")
            print(e)
            break

with opt(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO prescriptions (barcode, dose, time,leeway,as_needed,frequency) VALUES (%s,%s,%s,%s,%s,%s)",(row[1],int(row[2])),row[3] if row[3] else None, bool(row[4]),row[5] if row[5] else None)
        except Exception as e:
            print(f"Error in table prescriptions with row {row}")
            print(e)
            break

with open('database_setup/seeder_csvs/people.csv','r') as file:
    csvreader = csv.reader(file)

    next(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO people (name) VALUES (%s)",row[1::])
        except Exception as e:
            print(f"Error in table people with row {row}")
            print(e)
            break

with open('database_setup/seeder_csvs/assigned_prescriptions.csv','r') as file:
    csvreader = csv.reader(file)

    next(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO assigned_prescriptions (person_id,prescription_id) VALUES (%s,%s)",row)
        except Exception as e:
            print(f"Error in table assigned_prescriptions with row {row}")
            print(e)
            breaken('database_setup/seeder_csvs/prescriptions.csv','r') as file:
    csvreader = csv.reader(file)

    next(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO prescriptions (barcode, dose, time,leeway,as_needed,frequency) VALUES (%s,%s,%s,%s,%s,%s)",(row[1],int(row[2])),row[3] if row[3] else None, bool(row[4]),row[5] if row[5] else None)
        except Exception as e:
            print(f"Error in table prescriptions with row {row}")
            print(e)
            break

with open('database_setup/seeder_csvs/people.csv','r') as file:
    csvreader = csv.reader(file)

    next(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO people (name) VALUES (%s)",row[1::])
        except Exception as e:
            print(f"Error in table people with row {row}")
            print(e)
            break

with open('database_setup/seeder_csvs/assigned_prescriptions.csv','r') as file:
    csvreader = csv.reader(file)

    next(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO assigned_prescriptions (person_id,prescription_id) VALUES (%s,%s)",row)
        except Exception as e:
            print(f"Error in table assigned_prescriptions with row {row}")
            print(e)
            break

with open('database_setup/seeder_csvs/history.csv','r') as file:
    csvreader = csv.reader(file)

    next(csvreader)

    for row in csvreader:
        try:
            c.execute("INSERT INTO history (barcode,inventory_id,person_id,type_of_use,time_of_use,amnt_change,reason) VALUES (%s,%s,%s,%s,%s,%s,%s)",(row[1],int(row[2]),int(row[3]),row[4],row[5],int(row[6]),row[7] if row[7] else None,))
        except Exception as e:
            print(f"Error in table history with row {row}")
            print(e)
            break
    
conn.commit()
conn.close()