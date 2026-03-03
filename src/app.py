"""
Medical Inventory System - Kivy Application

Wires up the KV styles, widgets, and screens into a single App.
"""

import os
import sys

# Ensure src/ (and therefore sibling modules) is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

# KV must be loaded before any widget class that references KV rules
from kv_styles import KV                         # noqa: E402
# Widgets must be importable so the KV rules can find them
import widgets                                    # noqa: E402, F401
from screens import MainScreen, HistoryScreen, PersonalScreen  # noqa: E402

Builder.load_string(KV)


# ====================================================================== #
# region           APPLICATION                                            #
# ====================================================================== #

class MedicalInventoryApp(App):
    """Top-level Kivy application.

    Responsibilities
    ----------------
    * Set window appearance (colour, fullscreen).
    * Create the ScreenManager with all three screens.
    """

    title = 'Medical Inventory System'

    def build(self):
        """Configure the window and return the root ScreenManager.

        Returns
        -------
        ScreenManager
            Contains MainScreen, HistoryScreen, and PersonalScreen.
        """
        Window.clearcolor = (0.11, 0.11, 0.12, 1)
        try:
            Window.fullscreen = 'auto'
        except Exception:
            Window.size = (1280, 800)

        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(PersonalScreen(name='personal'))
        return sm

# endregion
