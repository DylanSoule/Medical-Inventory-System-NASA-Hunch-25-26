import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import csv

reader = SimpleMFRC522()
CSV = "scans.csv"

try:
    with open(CSV, "x", newline="") as f:
        import csv as _csv
        _csv.writer(f).writerow(["Timestamp","UID","Text"])
except FileExistsError:
    pass

print("Ready to scan. Press Ctrl+C to stop.")
try:
    while True:
        print("Hold an NFC sticker near the reader...")
        uid, text = reader.read()           # blocks until tag seen
        tag_text = text.strip() if isinstance(text, str) else ""
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] UID: {uid}  Text: {tag_text}")

        
        with open(CSV, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([ts, uid, tag_text])

        print("Logged to", CSV, "\n")
        time.sleep(1)   # small delay to avoid immediate duplicate reads

except KeyboardInterrupt:
    print("Stopping.")
finally:
    GPIO.cleanup()