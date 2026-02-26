"""
Medical Inventory System - Entry Point
NASA HUNCH Project 2025-26

Run this file to start the application.
All logic lives in the sub-modules — see:
    constants.py   – shared constants
    kv_styles.py   – Kivy KV layout strings
    widgets.py     – reusable UI widgets (popups, numpad, table rows)
    screens/       – one file per screen (main, history, personal)
    app.py         – MedicalInventoryApp (Kivy App subclass)
    database.py    – database access layer
    facial_recognition.py – face-recognition helpers
"""

import os
import sys

# Ensure src/ is on the import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import MedicalInventoryApp  # noqa: E402

if __name__ == '__main__':
    MedicalInventoryApp().run()
