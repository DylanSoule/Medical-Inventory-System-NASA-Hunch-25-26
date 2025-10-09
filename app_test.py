import tkinter as tk   # Import the tkinter module

# Create the main window
root = tk.Tk()
root.title("My First Tkinter App")

# Add a label (text)
label = tk.Label(root, text="Hello, World!", font=("Arial", 18))
label.pack(pady=10)

# Add a button that changes the text
def change_text():
    label.config(text="You clicked the button!")

button = tk.Button(root, text="Click Me", command=change_text)
button.pack(pady=10)

# Run the app
root.mainloop()