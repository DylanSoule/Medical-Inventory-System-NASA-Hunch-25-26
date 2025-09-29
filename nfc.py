from flask import Flask, request
import csv
import datetime

app = Flask(__name__)
CSV_FILE = "nfc_log.csv"

# Make sure file exists with header
with open(CSV_FILE, "a", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Timestamp", "TagData"])

@app.route("/log", methods=["POST"])
def log_nfc():
    data = request.json.get("tag", "UNKNOWN")
    timestamp = datetime.datetime.now().isoformat()

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, data])

    return {"status": "ok", "logged": data}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
