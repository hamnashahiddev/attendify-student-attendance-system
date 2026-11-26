# Troubleshooting Guide — Attendify

This guide provides solutions to common problems encountered while installing, running, and using **Attendify — Student Attendance Management System**.

If you encounter an issue that is not covered here, please open a GitHub Issue with the error message, steps to reproduce the problem, and relevant details about your environment.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Python & Django Issues](#python--django-issues)
- [Virtual Environment Issues](#virtual-environment-issues)
- [Database & Migration Issues](#database--migration-issues)
- [Authentication Issues](#authentication-issues)
- [Page & Template Issues](#page--template-issues)
- [Static Files Issues](#static-files-issues)
- [Server Issues](#server-issues)
- [Git & GitHub Issues](#git--github-issues)
- [General Debugging Tips](#general-debugging-tips)

---

## Installation Issues

### Python is not recognized

**Error:**

```text
'python' is not recognized as an internal or external command
```

**Solution:**

- Install Python from the official website.
- Enable the **Add Python to PATH** option during installation.
- Restart VS Code and verify:

```bash
python --version
```

### pip is not recognized

Try using pip through Python:

```bash
python -m pip --version
```

If pip is missing:

```bash
python -m ensurepip --upgrade
```

---

## Python & Django Issues

### Django is not installed

**Error:**

```text
ModuleNotFoundError: No module named 'django'
```

**Solution:**

Activate your virtual environment and install Django:

```bash
python -m pip install django
```

If the project contains a dependency file:

```bash
pip install -r requirements.txt
```

### Django admin command is not recognized

Instead of running `django-admin`, use:

```bash
python -m django --version
```

To create a Django project:

```bash
python -m django startproject config
```

---

## Virtual Environment Issues

### Virtual environment activation fails in PowerShell

If PowerShell blocks script execution, you can use Command Prompt:

```cmd
venv\Scripts\activate.bat
```

Alternatively, run Django directly through the virtual environment's Python:

```powershell
venv\Scripts\python.exe manage.py runserver
```

### Virtual environment is not activated

Check whether your terminal displays `(venv)` at the beginning of the command line.

If not, activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## Database & Migration Issues

### No such table error

**Possible cause:** Database migrations have not been applied.

**Solution:**

```bash
python manage.py migrate
```

### Model changes are not reflected in the database

Run:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Database migration conflicts

Check existing migration files and review the migration error before changing or deleting any migrations.

For a development database, backup important data before attempting to reset or recreate the database.

---

## Authentication Issues

### Login credentials are incorrect

- Verify your username and password.
- Ensure your account exists.
- If you manage the project locally, create an admin account:

```bash
python manage.py createsuperuser
```

### Access denied or permission errors

- Verify that you are logged in.
- Check the permissions associated with your account.
- Confirm that the page is accessible to your assigned role.

---

## Page & Template Issues

### TemplateDoesNotExist

**Possible cause:** Django cannot locate the requested template file.

**Solution:**

- Verify the template file exists.
- Check the template directory structure.
- Confirm the application is listed in `INSTALLED_APPS`.
- Check the template configuration in `settings.py`.
- Verify the template name used in your view.

### NoReverseMatch

**Possible cause:** Django cannot resolve a URL pattern using the provided name or parameters.

**Solution:**

- Verify the URL pattern name.
- Check the URL arguments and parameters.
- Confirm the URL namespace is correct.
- Review the `{% url %}` template tag.

### Page displays incorrect or missing information

- Check the view function or class.
- Verify the context data passed to the template.
- Confirm the database contains the expected records.
- Check variable names used inside the template.

---

## Static Files Issues

### CSS or JavaScript is not loading

**Solution:**

- Verify the static file exists.
- Check `STATIC_URL` and `STATICFILES_DIRS` in `settings.py`.
- Confirm the template uses Django's static template tag.

Example:

```django
{% load static %}
<link rel="stylesheet" href="{% static 'css/style.css' %}">
```

During local development, ensure static file configuration is correct and restart the server if needed.

---

## Server Issues

### Port 8000 is already in use

Run the server on another port:

```bash
python manage.py runserver 8001
```

### Server starts but the page does not open

- Confirm the development server is running.
- Check the URL in the terminal.
- Try opening:

```text
http://127.0.0.1:8000/
```

- Check terminal output for errors.

### Error 500 — Internal Server Error

- Review the terminal traceback.
- Check the view, template, database query, and related code.
- Reproduce the error and inspect the exact failing line.
- Avoid guessing; use the traceback to locate the issue.

### Error 404 — Page Not Found

- Verify the requested URL.
- Check `urls.py`.
- Ensure the route exists and is correctly configured.

---

## Git & GitHub Issues

### Git is not recognized

Install Git and restart VS Code.

Verify installation:

```bash
git --version
```

### Changes are not appearing on GitHub

Run:

```bash
git status
git add .
git commit -m "Update Attendify project"
git push
```

Ensure your local branch is connected to the correct remote repository.

### Push rejected

Your local branch may be behind the remote branch.

Try:

```bash
git pull --rebase origin main
git push
```

If conflicts occur, resolve them before pushing again.

---

## General Debugging Tips

When troubleshooting Attendify:

1. Read the complete error message.
2. Check the VS Code terminal output.
3. Identify the file and line where the error occurs.
4. Confirm your virtual environment is activated.
5. Check that dependencies are installed.
6. Verify database migrations.
7. Test one change at a time.
8. Restart the development server when necessary.
9. Avoid deleting database or migration files without a backup.

When asking for help, provide:

- The error message or traceback.
- What you were trying to do.
- What you expected to happen.
- What actually happened.
- Screenshots if the issue is related to the interface.

---

## Need More Help?

If your issue persists, open an issue in the Attendify GitHub repository and include enough information to reproduce it.

**Project Maintainer:** Hamna Shahid  
**GitHub:** [@hamnashahiddev](https://github.com/hamnashahiddev)

---

*Attendify — Student Attendance Management System*
