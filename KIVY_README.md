# Medical Inventory System - Kivy Version

This is a Kivy-based implementation of the Medical Inventory System for NASA HUNCH Project 2025-26.

## Overview

The Kivy version provides the same functionality as the original Tkinter/CustomTkinter version but with a modern, cross-platform UI framework that works well on:
- Desktop (Linux, Windows, macOS)
- Raspberry Pi
- Touch-enabled devices

## Features

- ✅ **Inventory Management**: View and manage medical inventory with real-time updates
- ✅ **Barcode Scanning**: Add, remove, or use items via barcode
- ✅ **Facial Recognition**: Identify users through facial recognition
- ✅ **Advanced Filtering**: Search and filter by multiple criteria
- ✅ **Transaction History**: Track all inventory changes
- ✅ **Column Customization**: Show/hide columns as needed
- ✅ **Responsive Design**: Adapts to different screen sizes
- ✅ **Keyboard Shortcuts**: F11 for fullscreen, Escape to exit

## Installation

### 1. Install System Dependencies (Linux/Raspberry Pi)

```bash
# Update package lists
sudo apt-get update

# Install Python dependencies
sudo apt-get install -y python3-dev python3-pip

# Install Kivy dependencies
sudo apt-get install -y \
    libgl1-mesa-dev \
    libgles2-mesa-dev \
    libgstreamer1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libmtdev1 \
    build-essential \
    libssl-dev \
    libffi-dev \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev
```

### 2. Install Python Packages

```bash
# Navigate to project directory
cd Medical-Inventory-System-NASA-Hunch-25-26

# Install Python requirements
pip3 install -r requirements.txt
```

### 3. Setup Database

The database will be automatically created on first run. It's located at `Database/inventory.db`.

## Running the Application

### Standard Run

```bash
python3 src/medical_inventory_kivy.py
```

### Fullscreen Mode

The application starts in windowed mode. Press **F11** to toggle fullscreen, or **Escape** to exit fullscreen.

### For Raspberry Pi (Optimized)

```bash
# Set environment variables for better performance
export KIVY_WINDOW=sdl2
export KIVY_GL_BACKEND=gl

python3 src/medical_inventory_kivy.py
```

## Usage Guide

### Main Interface

The interface is divided into three main sections:

1. **Left Sidebar**: Controls and filters
   - Search box for filtering items
   - Filter options (All, Expiring Soon, Expired)
   - Low stock filter
   - Column visibility toggles
   - Action buttons

2. **Right Panel**: Data table showing inventory
   - Scrollable list of all items
   - Sortable columns
   - Color-coded status

3. **Bottom Status Bar**: System status indicators
   - Camera status
   - Face recognition status
   - Database status

### Barcode Scanning

1. Click **"Scan Barcode"** button
2. Enter the barcode
3. Select action:
   - Add to Inventory
   - Remove from Inventory
   - Use Item
4. Enter user name
5. Click Submit

### Face Recognition

1. Click **"Face Recognition"** button
2. Position face in front of camera
3. System will identify the user

### Adding New Drugs

1. Click **"Add New Drug"** button
2. Fill in all required fields:
   - Barcode
   - Drug Name
   - Amount
   - Expiration Date (YYYY-MM-DD)
   - Type
   - Dose Size
   - Item Type
3. Click "Add Drug"

### Viewing History

1. Click **"View History"** button
2. Browse the last 50 transactions
3. Each entry shows:
   - Timestamp
   - Drug name and barcode
   - Change amount
   - User who made the change
   - Reason (if provided)

## Configuration

### Window Settings

Edit the file to customize window behavior:

```python
# In MedicalInventoryApp.build()
Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Background color
Window.fullscreen = False  # Start in fullscreen
```

### Data Refresh Interval

```python
REFRESH_INTERVAL = 30  # seconds
```

### Column Configuration

Modify the `COLUMNS` list to add/remove/reorder columns:

```python
COLUMNS = [
    {"id": "drug", "label": "Drug", "width": 220},
    {"id": "barcode", "label": "Barcode", "width": 170},
    # Add more columns as needed
]
```

## Comparison with Tkinter Version

### Advantages of Kivy Version

1. **Cross-Platform**: Works on more platforms including mobile (with modifications)
2. **Touch Support**: Native touch screen support
3. **Modern UI**: More modern and customizable appearance
4. **Better Graphics**: Hardware-accelerated graphics
5. **Scalability**: Better DPI scaling on different displays
6. **Theming**: Easier to customize colors and themes

### Differences

1. **Look & Feel**: Different visual style compared to CustomTkinter
2. **Widgets**: Uses Kivy widgets instead of Tkinter/CustomTkinter
3. **Event Handling**: Different event system (Kivy properties and events)
4. **Threading**: Uses Kivy's Clock and @mainthread decorator

## Troubleshooting

### Application Won't Start

```bash
# Check Kivy installation
python3 -c "import kivy; print(kivy.__version__)"

# If it fails, reinstall Kivy
pip3 install --upgrade kivy
```

### Camera Not Detected

- Ensure camera is connected
- Check camera permissions
- Try different camera indices in facial_recognition.py

### Face Recognition Not Working

- Verify reference images are in `assets/references/`
- Check that InsightFace models are downloaded
- Ensure adequate lighting

### Performance Issues

On Raspberry Pi, try:

```bash
# Reduce window size
# In medical_inventory_kivy.py, modify Window settings:
Window.size = (1024, 600)

# Use simpler graphics backend
export KIVY_GL_BACKEND=gl
```

### Database Errors

```bash
# Check database file exists and is writable
ls -l Database/inventory.db

# Recreate database if corrupted
rm Database/inventory.db
python3 src/medical_inventory_kivy.py
```

## Keyboard Shortcuts

- **F11**: Toggle fullscreen mode
- **Escape**: Exit fullscreen mode
- **Tab**: Navigate between input fields
- **Enter**: Submit forms (when in text input)

## Development

### Project Structure

```
Medical-Inventory-System-NASA-Hunch-25-26/
├── src/
│   ├── medical_inventory.py         # Original Tkinter version
│   ├── medical_inventory_kivy.py    # New Kivy version
│   └── facial_recognition.py        # Shared facial recognition module
├── Database/
│   ├── database.py                  # Shared database module
│   └── inventory.db                 # SQLite database
├── assets/
│   └── references/                  # Face recognition reference images
└── requirements.txt                 # Python dependencies
```

### Extending the Application

To add new features:

1. **New Column**: Add to `COLUMNS` list
2. **New Filter**: Modify `apply_filters()` method
3. **New Action**: Add button in `create_sidebar()` and handler method
4. **Custom Widget**: Create new class inheriting from Kivy widgets

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the original documentation in `README.md`
3. Check Kivy documentation: https://kivy.org/doc/stable/

## License

Same as the original Medical Inventory System project.

## Credits

- Original Tkinter version: Medical Inventory System Team
- Kivy conversion: Updated for NASA HUNCH 2025-26
- Framework: Kivy (https://kivy.org)
