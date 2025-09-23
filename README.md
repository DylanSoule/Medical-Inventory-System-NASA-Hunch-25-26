# Medical Inventory System — NASA Hunch 25‑26

A web-based and AI‑powered medical inventory system incorporating facial recognition for secure access. Built as part of the NASA Hunch 2025‑2026 program.

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
- Web UI with responsive design  
- Real‑time alerts for low stock  
- Logging of user actions  

## Architecture & Components

| Component | Description |
|---|---|
| `index.html` / `style.css` | Frontend UI for interacting with the system |
| `facialrecognition.py` | Python script to handle face detection, identification, and authentication |
| `references/` folder (not shown in repo) | Contains reference images of authorized users for face matching |

Languages used: **Python**, **HTML**, **CSS**

## Getting Started

### Prerequisites

- Python 3.10 or newer  
- Pip (Python package manager)  
- A webcam or camera for facial recognition (if testing live)  
- Clear, forward-facing facial images for each authorized user  

### Installation & Setup

1. Clone this repository  
   ```bash
   git clone https://github.com/ltl902/Medical-Invintory-System-NASA-Hunch-25-26-.git
   cd Medical-Invintory-System-NASA-Hunch-25-26-
   ```

2. Install Python dependencies  
   ```bash
   pip install numpy opencv-python insightface
   ```  
   (Use `--user` if not installing system-wide.)

3. Prepare reference images  
   - Create a folder named `references/`  
   - Add clear photos of each authorized user (frontal view, good lighting)  

### Usage

- Run the facial recognition authentication  
  ```bash
  python facialrecognition.py
  ```
  The script will compare a live image or test image to stored references; on match, it grants access.

- Use the web frontend (`index.html`) to manage inventory: add/remove items, view stock, etc.

## Facial Recognition Module

The `facialrecognition.py` script handles:

- Loading reference images  
- Capturing an input image (or reading from file)  
- Using **InsightFace** and **OpenCV** to detect and match faces  
- Validating identity before granting access to the inventory interface  

### Notes & Tips

- Use high-quality, well-lit reference images  
- Ensure the test image is similar in lighting and angle to reference images  
- You may need to calibrate thresholds for face matching accuracy  

## Project Status

This is currently a **proof-of-concept / prototype**. Next steps could include:

- Backend database integration (e.g. SQLite, PostgreSQL)  
- REST API endpoints  
- More robust user management (roles, permissions)  
- Better UI/UX and responsive layout  
- Security improvements (e.g. encryption, audit trails)  

## Contributing

We welcome contributions! If you’d like to help:

1. Fork the repository  
2. Create a feature branch (`git checkout -b feat‑name`)  
3. Make your changes and commit with clear messages  
4. Submit a pull request  

Please ensure major new features come with tests or usage demos.

## Resources

- Schedule & planning: [Trello](https://trello.com)  
- Research: [Google Docs](https://docs.google.com)  
- Brainstorming: [Miro](https://miro.com)  
- PRD: [Google Docs](https://docs.google.com)  

## License

Specify your license here (e.g. MIT, Apache 2.0, etc.).  
