# Installation Guide — Attendify

This guide explains how to install, configure, and run **Attendify — Student Attendance Management System** on your local machine for development and testing.

## Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Clone the Repository](#clone-the-repository)
- [Windows Installation](#windows-installation)
- [macOS and Linux Installation](#macos-and-linux-installation)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Accessing Attendify](#accessing-attendify)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

Attendify is a Django-based web application for student attendance tracking and academic management.

The system includes student management, teacher management, attendance records, classrooms, subjects, timetables, reports, announcements, and dashboards.

---

## Prerequisites

Before installing Attendify, make sure you have the following installed:

| Requirement | Description |
|---|---|
| Python 3.10+ | Python programming language |
| Git | Version control and repository cloning |
| pip | Python package manager |
| VS Code (optional) | Recommended development editor |
| Web Browser | For accessing the application |

Check Python installation:

```bash
python --version
```

Check Git installation:

```bash
git --version
```

Check pip:

```bash
pip --version
```

---

## Clone the Repository

Clone the Attendify repository from GitHub:

```bash
git clone https://github.com/hamnashahiddev/attendify-student-attendance-system.git
```

Navigate to the project directory:

```bash
cd attendify-student-attendance-system
```

---

## Windows Installation

### Step 1: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 2: Activate the Virtual Environment

Using Windows Command Prompt:

```cmd
venv\Scripts\activate.bat
```

Using PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation because of execution policies, you can use Command Prompt or activate the environment using:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 3: Install Dependencies

If `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

If the project does not include a requirements file, install Django:

```bash
pip install django
```

---

## macOS and Linux Installation

### Step 1: Create a Virtual Environment

```bash
python3 -m venv venv
```

### Step 2: Activate the Virtual Environment

```bash
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is unavailable:

```bash
pip install django
```

---

## Database Setup

Attendify uses SQLite as its default database for local development.

Run the database migrations:

```bash
python manage.py migrate
```

This command creates and updates the database tables required by the application.

### Optional: Create an Administrator Account

To access Django's administrative interface, create a superuser:

```bash
python manage.py createsuperuser
```

Follow the prompts to enter your username, email, and password.

---

## Running the Application

Start the local Django development server:

```bash
python manage.py runserver
```

To run the server on a specific port:

```bash
python manage.py runserver 8080
```

To access the application from another device on your local network (development only):

```bash
python manage.py runserver 0.0.0.0:8000
```

---

## Accessing Attendify

Once the server is running, open your browser and visit:

**Main Application:**

http://127.0.0.1:8000/

**Django Admin:**

http://127.0.0.1:8000/admin/

The admin panel requires a superuser account.

---

## Troubleshooting

### Python is not recognized

Install Python and ensure the option **Add Python to PATH** is selected during installation.

### Django is not installed

Run:

```bash
pip install django
```

### Dependencies installation fails

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Then reinstall the requirements:

```bash
pip install -r requirements.txt
```

### Database errors

Run migrations again:

```bash
python manage.py migrate
```

### Port 8000 is already in use

Run the application on another port:

```bash
python manage.py runserver 8001
```

### Virtual environment activation fails in PowerShell

Use Command Prompt instead:

```cmd
venv\Scripts\activate.bat
```

Or run the virtual environment's Python directly:

```powershell
venv\Scripts\python.exe manage.py runserver
```

---

## Development Notes

- This installation is intended for local development and testing.
- Do not commit virtual environments, secret keys, passwords, or private data.
- Do not use real student information in development environments.
- Before deploying publicly, configure production security, environment variables, HTTPS, database backups, and a production server.

---

**Attendify — Student Attendance Management System**

Developed by [Hamna Shahid](https://github.com/hamnashahiddev).
