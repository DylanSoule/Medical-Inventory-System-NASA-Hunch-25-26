#NOT UP TO DATE



# Medical Inventory System — NASA Hunch 25‑26

An AI‑powered medical inventory system incorporating facial recognition for secure access. Built as part of the NASA Hunch 2025‑2026 program.

## Table of Contents

- [About](#about)  
- [Features](#features)  
- [Architecture & Components](#architecture--components)  
- [Getting Started](#getting-started)  
  - [Prerequisites](#prerequisites)  
  - [Installation & Setup](#installation--setup)  
  - [Usage](#usage)  
- [Facial Recognition Module](#facial-recognition-module)  
- [Project Status](#project-status)  
- [Contributing](#contributing)  
- [Resources](#resources)  
- [License](#license)  

## About

The Medical Inventory System is designed to help medical facilities (or mobile units) track supplies, manage stock levels, and control access securely using facial recognition. The system was developed during NASA’s Hunch program cycle 2025‑26 as part of a team project.  

## Features

- Inventory listing, addition, removal, and auditing  
- Secure login via facial recognition  
- UI with responsive design  
- Real‑time alerts for low stock  
- Logging of user actions  

## Architecture & Components

| Component | Description |
|---|---|
| `facial_recognition.py` | Python script to handle face detection, identification, and authentication |
| `medical_inventory.py` | Frontend UI to hadle user input and logging of scans


### Prerequisites for facial recognition authentication

- Python 3.10 or newer  
- Pip (Python package manager)  
- A webcam or camera for facial recognition
- Clear, forward-facing facial images for each authorized user  

### Installation & Setup

1. Clone this repository  
   ```bash
   git clone https://github.com/ltl902/Medical-Invintory-System-NASA-Hunch-25-26-.git
   cd Medical-Invintory-System-NASA-Hunch-25-26-
   ```

2. Install Python dependencies  
   ```pip install numpy opencv-python insightface onnxruntime```  



4. Prepare reference images  
   - Create a folder named `references`  
   - Add clear photos of each authorized user to the folder (frontal view, good lighting)  

### Usage

- Run the medical inventory app   
  ```python3 medical_inventory.py```

  
  The script will compare a live image or test image to stored references; on match, it grants access.

- Use the frontend (`medical_inventory.py`) to manage inventory: add/remove items, view stock, etc.



## Resources

- Schedule & planning: [Trello](https://trello.com/b/H7cOixDG/medical-inventory-system-nasa-hunch)  
- Research: [Google Doc](https://docs.google.com/document/d/1bPDbMDzeHgcyTJU0ENFX7s9UR9npXHJ3vHZIvmdP6Yc/edit?usp=sharing)  
- Brainstorming: [Miro](https://miro.com/app/board/uXjVJIvb3LU=/)  

## License


