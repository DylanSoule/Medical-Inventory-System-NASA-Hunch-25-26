"""
Medical Inventory System - Shared Constants
"""

REFRESH_INTERVAL = 300  # seconds between auto-refresh

ADMIN_CODE = "1234"

# (column_id, display_label, default_width)
COLUMNS = [
    ("drug",       "Drug",       220),
    ("barcode",    "Barcode",    170),
    ("est_amount", "Amt~",       100),
    ("exp_date",   "Expiration", 140),
    ("type_",      "Type",       120),
    ("dose_size",  "Dose Size",  140),
    ("item_loc",   "Location",   100),
]
