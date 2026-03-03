"""
Medical Inventory System - Shared Constants

Centralised values imported by screens, widgets, and app.
Change them here and every consumer picks up the update.
"""


# ====================================================================== #
# region           TIMING                                                 #
# ====================================================================== #

REFRESH_INTERVAL = 300
"""int: Seconds between automatic data refreshes on MainScreen."""

# endregion


# ====================================================================== #
# region           AUTHENTICATION                                         #
# ====================================================================== #

ADMIN_CODE = "1234"
"""str: PIN required for admin-gated actions (delete, etc.)."""

# endregion


# ====================================================================== #
# region           TABLE COLUMNS                                          #
# ====================================================================== #

COLUMNS = [
    # (column_id,     display_label, default_width_dp)
    ("type_",        "Type",        220),
    ("drug",         "Drug",        170),
    ("barcode",      "Barcode",     100),
    ("est_amt",      "Amt~",        140),
    ("exp_date_raw", "Expiration",  120),
    ("dose_size",    "Dose Size",   140),
    ("item_loc",     "Location",    100),
]
"""list[tuple[str, str, int]]: Inventory table column definitions.

Each tuple: ``(column_id, display_label, default_width_dp)``.
``column_id`` matches the database field name used in queries.
``display_label`` is shown in the header row.
``default_width_dp`` sets the initial column width in density-independent pixels.
"""

# endregion
