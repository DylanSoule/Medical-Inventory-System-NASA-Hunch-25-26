import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import os
import sys
import datetime
import tkcalendar as cal

class PersonalWindowLoader:
    def __init__(self, master):
        self.master = master
        self.master.title("Personal Window Loader")
        self.master.geometry("400x300")
        self.label = ctk.CTkLabel(master, text="This is the Personal Window Loader")
        self.label.pack(pady=20)
        self.button = ctk.CTkButton(master, text="Close", command=self.master.destroy)
        self.button.pack(pady=10)

if __name__ == "__main__":
    root = ctk.CTk()
    app = PersonalWindowLoader(root)
    root.mainloop()