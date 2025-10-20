h2 {

}
# Medical Inventory System — NASA Hunch 2025-26

A medical inventory system incorporating barcoding for tracking inventory as well as facial recognition for secure access. The project was built as part of the NASA Hunch 2025‑2026 program.  
The app and AI-powered facial recognition software runs on a raspberry pi in order to allow for efficient and low energy running so it can be installed on space stations or long term space missions without major concern for energy pull.

**Note** This project is still under development

## Table of Contents

- [About](#about)
- [Features](#features)
- [Architecture & Components](#architecture--components)
- [System Flowchart](#system-flowchart)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
   - [Usage](#usage)
- [Facial Recognition Module](#facial-recognition-module)
- [Project Status](#project-status)
- [License](#license)
- [Contact Info](#contact-info)

---

## About
The **Medical Inventory System** is designed to help medical facilities, specifically ones on space stations on aboard space mission, track supplies, manage stock levels, and control access securely using facial recognition.  
Developed for the **NASA Hunch 2025-26** program, the system runs efficiently on a **Raspberry Pi** or similar embedded device — suitable for low-power, remote, or space environments.


## Features
### Current
- In-app barcode scanning for adding/removing medical items.
- Facial recognition to authenticate users.
- Automatic CSV logging of all inventory actions.
- Real-time display of current inventory in a GUI.

### Planned / Future
- Search and filter inventory records.
- Edit and delete individual entries.
- Alerts for low stock or expired items.
- Cloud dashboard for mission monitoring.
- Role-based access control (Admin / User).


## Architecture & Components
| Component | Description |
|---|---|
| `medical_inventory.py` | Main GUI and logic for barcode + inventory management. |
| `facial_recognition.py` | Handles user authentication via camera and InsightFace. |
| `scans.csv` | Local data file that stores all inventory transactions. |
| `references/` | Directory containing facial reference images for authorized users. |
| Hardware | Raspberry Pi (or PC), USB barcode scanner, and camera module. |


## System Flowchart
Below is a visual overview of how the system operates from authentication to inventory management.

```mermaid
flowchart TD
    A[Start System] --> B[Initialize Camera & Barcode Scanner]
    B --> C[Facial Recognition and Identification]
    C --> D[Open Inventory Dashboard]
    D --> E[Log who accessed system]
    D --> F[User Scans Item Barcode]
    E --> G
    F --> G{Action Type?}
    G -->|Add Item| H[Append Entry to CSV + Update Count]
    G -->|Remove Item| I[Subtract From Count + Log Action]
    H --> J[Display Updated Inventory]
    I --> J[Display Updated Inventory]
    J --> K[Option: Search / Edit / Export CSV]
    K --> L[Save Changes and Log Event]
```

> The flow above represents how user authentication, barcode scanning, and logging interact in the overall system workflow.


## Prerequisites
- Python 3.10 +  
- Pip package manager  
- Camera (USB or Pi Camera)  
- Barcode scanner  
- `insightface`, `onnxruntime`, `opencv-python`, `numpy`

### Prerequisites for facial recognition authentication
  
- A webcam or camera for facial recognition
- Clear, forward-facing facial images for each authorized user  
- Connect your camera and barcode scanner before running.


## Installation & Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/ltl902/Medical-Inventory-System-NASA-Hunch-25-26-
   cd Medical-Inventory-System-NASA-Hunch-25-26-
   ```

2. Install dependencies:
   ```bash
   pip install numpy opencv-python insightface onnxruntime python3-tk
   ```
### Setting up facial recognition
3. Prepare facial recognition data:
   - Add authorized user photos in a folder named `references/`.
   - Use clear, frontal images with consistent lighting.

4. Connect your camera and barcode scanner before running.

### Usage
Run the main system:
```bash
python3 medical_inventory.py
```

- The app will start the camera and prompt for facial authentication.
- Once verified, the dashboard opens for scanning and managing items.
- Each transaction is saved to `scans.csv` automatically.

Run facial recognition independently:
```bash
python3 facial_recognition.py
```

## Facial Recognition Module
This module uses **InsightFace** with **ONNX Runtime** for lightweight, on-device face matching.

### Steps
1. Capture live image from camera.  
2. Detect face and compute facial embeddings.  
3. Compare embeddings with saved user database.  
4. Grant or deny access based on match threshold.


## Project Status
**In Development** — actively improving:
- Bug fixes for barcode UI.
- Add/Delete/Edit features for CSV entries.
- Search and filtering interface.

## License
This project is open source under the **MIT License**.  
See [LICENSE](LICENSE) for details.

## Contact Info
**NASA Hunch 2025-26 Medical Inventory Team**  
- Maintainers: `Dylan Soule, Brody Barnes, Lucca Townsend, Zach Stelman`  
- Email: `dylan.soule@icloud.com`  
- GitHub: [ltl902](https://github.com/ltl902)
- Brainstorming: [Miro](https://miro.com/app/board/uXjVJIvb3LU=/)  
