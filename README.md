# 🛡️ Smart Monitoring and Security System

> **Project Banner Placeholder**
>
> *(Insert project banner image here.)*

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-Database-orange?logo=mysql)
![ESP32](https://img.shields.io/badge/ESP32-IoT-red)
![Arduino](https://img.shields.io/badge/Arduino-Firmware-00979D?logo=arduino)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Completed-success)

A full-stack Internet of Things (IoT) monitoring platform that integrates ESP32 microcontrollers, environmental sensors, an ESP32-CAM, a Flask backend, and a MySQL database to provide real-time monitoring, security alerts, and data analytics through a responsive web dashboard.

---

# 📑 Table of Contents

- [Repository Highlights](#-repository-highlights)
- [Overview](#-overview)
- [Features](#-features)
- [Hardware Components](#-hardware-components)
- [Software Stack](#-software-stack)
- [Built With](#-built-with)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [System Workflow](#-system-workflow)
- [REST API](#-rest-api)
- [Database](#-database)
- [Screenshots](#-screenshots)
- [Key Learning Outcomes](#-key-learning-outcomes)
- [Future Improvements](#-future-improvements)
- [Project Team](#-project-team)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

# 🚀 Repository Highlights

- Complete IoT monitoring and security solution
- Full-stack architecture integrating embedded systems and web technologies
- Real-time environmental and security monitoring
- RESTful API communication between ESP32 devices and Flask
- Secure user authentication and role-based sensor permissions
- Interactive analytics dashboard
- MySQL database integration
- Modular firmware for individual sensors
- Responsive web interface
- Team-based engineering project

---

# 📖 Overview

The **Smart Monitoring and Security System (SMSAM)** is a comprehensive IoT solution designed to monitor environmental conditions and detect security events in real time.

Multiple ESP32-based devices collect data from connected sensors and transmit the readings to a Flask REST API using HTTP requests. The backend validates incoming data before storing it in a MySQL database. Users can securely log into a web dashboard to monitor live sensor readings, review historical information, and generate analytics through an integrated reporting module.

The project demonstrates the integration of embedded systems, networking, backend development, database management, web technologies, and data analytics into a complete end-to-end monitoring platform.

---

# ✨ Features

- 🔐 Secure user authentication
- 📡 Real-time sensor monitoring
- 🌡 Temperature monitoring
- 💧 Humidity monitoring
- 💡 Ambient light detection
- 🚶 Motion detection
- 📏 Distance measurement
- 📷 ESP32-CAM integration
- 📊 Analytics dashboard with automatically generated graphs
- 💾 Persistent MySQL database storage
- 🌐 REST API communication using JSON
- 📱 Responsive web interface

---

# 🛠 Hardware Components

| Component | Purpose |
|------------|---------|
| ESP32 | Main microcontroller |
| ESP32-CAM | Image capture and surveillance |
| DHT22 | Temperature and humidity monitoring |
| PIR Sensor | Motion detection |
| HC-SR04 | Distance measurement |
| LDR | Ambient light monitoring |
| Breadboard | Hardware prototyping |
| Jumper Wires | Sensor connections |
| USB Cable | Programming and power |

---

# 💻 Software Stack

| Category | Technologies |
|----------|--------------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | MySQL |
| Firmware | Arduino IDE (C++) |
| Analytics | Pandas, NumPy, Matplotlib, Seaborn |
| Communication | HTTP REST API |
| Data Format | JSON |
| Version Control | Git & GitHub |

---

# ⚙ Built With

- Python
- Flask
- SQLAlchemy
- MySQL
- HTML5
- CSS3
- JavaScript
- ESP32
- ESP32-CAM
- Arduino IDE
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Git
- GitHub

---

# 🏗 System Architecture

<img width="601" height="413" alt="image" src="https://github.com/user-attachments/assets/947e42c9-a97a-4e7f-8c76-5d2f6a179a18" />

```

# 📂 Project Structure

```text
smart-monitoring-security-system/
│
├── backend/
│   ├── static/
│   ├── templates/
│   ├── .env.example
│   ├── analytics_manager.py
│   ├── app.py
│   └── requirements.txt
│
├── database/
│   └── smam_database.sql
│
├── firmware/
│   ├── CameraWebServer/
│   ├── smsam_dht22/
│   ├── smsam_ldr/
│   ├── smsam_pir/
│   └── smsam_ultrasonic/
│
├── LICENSE
└── README.md
```

---

# 📡 System Workflow

1. Sensors collect environmental and security data.
2. ESP32 microcontrollers process the sensor readings.
3. Data is packaged into JSON format.
4. HTTP requests transmit the data to the Flask backend.
5. The backend validates and stores the information in MySQL.
6. The dashboard retrieves live and historical data.
7. The analytics engine generates reports and visualizations.
8. Users monitor the system through the web interface.

**Workflow Diagram Placeholder**

---

# 🌐 REST API

The Flask backend exposes REST endpoints for communication between the embedded hardware and the web application.

The API supports:

- User authentication
- Temperature and humidity submission
- Motion detection events
- Distance sensor updates
- Light intensity monitoring
- ESP32-CAM integration
- Analytics generation
- Retrieval of the latest sensor readings

---

# 🗄 Database

The MySQL database stores:

- User accounts
- Temperature readings
- Humidity readings
- Motion detection events
- Distance measurements
- Light intensity readings
- Camera information
- Analytics data

The database schema is provided in:

```text
database/smam_database.sql
```

---

# 📸 Screenshots

## Login Page

<img width="1676" height="926" alt="Screenshot 2026-08-06 151434" src="https://github.com/user-attachments/assets/2ed4f78d-f497-4667-9861-fe3a688d267d" />

---

## Dashboard

<img width="1660" height="926" alt="Screenshot 2026-08-06 151542" src="https://github.com/user-attachments/assets/48ac4469-4506-4af9-8e90-dcb5499b5627" />

---

## Temperature & Humidity Monitoring

<img width="1664" height="926" alt="Screenshot 2026-08-06 151606" src="https://github.com/user-attachments/assets/6e1b763e-f5ca-438b-9ee6-5a20245240df" />
<img width="1664" height="928" alt="Screenshot 2026-08-06 151755" src="https://github.com/user-attachments/assets/f14bb63b-dfb0-4ce6-ac22-eee53ece93d6" />

---

## Motion Detection

<img width="1662" height="926" alt="Screenshot 2026-08-06 151807" src="https://github.com/user-attachments/assets/315878a8-ae33-4b5a-b9d0-38e558fb964a" />

---

## Analytics Dashboard

<img width="1666" height="928" alt="Screenshot 2026-08-06 151919" src="https://github.com/user-attachments/assets/c477e78c-ae3f-45e1-a2d5-7702d30722ab" />

---

## Database Tables

<img width="1972" height="1118" alt="Screenshot 2026-08-06 152606" src="https://github.com/user-attachments/assets/5f17a5c2-d2aa-4bb7-9e77-b05b119064f3" />

---

## ESP32-CAM

**Screenshot Placeholder**

---

# 🎯 Key Learning Outcomes

This project provided practical experience in:

- Embedded systems programming using ESP32
- Multi-sensor hardware integration
- RESTful API development
- Backend development using Flask
- MySQL database design and integration
- Data analytics using Python
- Real-time communication using HTTP and JSON
- Responsive web development
- IoT system architecture
- Git and GitHub version control
- Collaborative software development

---

# 🔮 Future Improvements

- Mobile application support
- MQTT communication
- Cloud deployment
- Push notifications
- AI-powered anomaly detection
- Enhanced role-based access control
- Device management dashboard
- Expanded camera analytics

---

# 👥 Project Team

This project was developed collaboratively as part of an engineering team.

|Team Member |
|-----------------|
| Rhema Miller 
| Doctor Mkhonza 
| Karabelo Motaung 
| Moleboge Setjie 
| Thifhindulwi Tuwane

---

# 🤝 Contributing

This project was developed as an academic engineering project and is presented as a portfolio showcase.

Suggestions, improvements, and constructive feedback are always welcome. Feel free to open an issue or submit a pull request.

---

# 📄 License

This project is licensed under the MIT License.

See the **LICENSE** file for more information.

---

# 📬 Contact

If you have any questions about this project, suggestions for improvement, or would like to collaborate, feel free to connect with me through GitHub.

Feedback and constructive suggestions are always appreciated.
