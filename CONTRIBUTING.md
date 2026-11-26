# Contributing to Attendify

Thank you for your interest in contributing to **Attendify — Student Attendance Management System**! Contributions, suggestions, bug reports, and improvements are welcome. This document explains how to contribute to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Code Guidelines](#code-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

## Getting Started

Before contributing, please:

- Check the existing issues and pull requests to avoid duplicate work.
- Read the project's README.md to understand its purpose and features.
- Make sure you have Git, Python, and Django installed.
- Review the CODE_OF_CONDUCT.md before participating.

## Development Setup

### 1. Fork the Repository

Fork the Attendify repository to your GitHub account.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/attendify-student-attendance-system.git
```

Navigate to the project directory:

```bash
cd attendify-student-attendance-system
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Activate it on macOS/Linux:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

If the project contains a requirements.txt file:

```bash
pip install -r requirements.txt
```

### 5. Apply Migrations

```bash
python manage.py migrate
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

Open the application in your browser:

http://127.0.0.1:8000/

## How to Contribute

### 1. Create a Branch

Create a separate branch for your contribution:

```bash
git checkout -b feature/your-feature-name
```

For bug fixes:

```bash
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Keep changes focused on one feature or issue.
- Avoid modifying unrelated files.
- Follow the existing project structure and coding style.
- Test your changes before submitting.

### 3. Commit Your Changes

Use clear and descriptive commit messages:

```bash
git add .
git commit -m "Add descriptive commit message"
```

### 4. Push Your Branch

```bash
git push origin feature/your-feature-name
```

### 5. Open a Pull Request

Create a pull request from your branch to the main branch of the original repository.

Include:

- A clear description of your changes.
- The problem your contribution solves.
- Screenshots for UI changes when applicable.
- Steps to test your changes.

## Reporting Bugs

If you discover a bug, please open a GitHub Issue and include:

- A clear and descriptive title.
- Steps to reproduce the problem.
- Expected behavior.
- Actual behavior.
- Screenshots or error messages, if available.
- Relevant environment information, such as OS and Python version.

Please search existing issues before submitting a new one.

## Suggesting Features

Feature suggestions are welcome!

When proposing a new feature:

- Explain the problem it solves.
- Describe the proposed functionality.
- Explain how it would improve Attendify.
- Include mockups or examples if useful.

Open a GitHub Issue to discuss the idea before starting major development work.

## Code Guidelines

### Python & Django

- Follow PEP 8 Python coding conventions.
- Use descriptive names for variables, functions, and classes.
- Keep functions and views focused on a single responsibility.
- Use Django's built-in features wherever appropriate.
- Avoid unnecessary dependencies.
- Handle errors and user input carefully.

### Frontend

- Keep the interface clean, responsive, and accessible.
- Maintain consistency with the existing design system.
- Ensure pages work across different screen sizes.
- Avoid unnecessary changes to existing UI components.

### Security

- Never commit passwords, secret keys, API tokens, or sensitive environment variables.
- Do not upload private student information or real attendance records.
- Validate user inputs and protect sensitive operations.
- Follow Django security best practices.

## Commit Message Guidelines

Use simple, meaningful commit messages.

Examples:

- `Add student attendance report feature`
- `Fix teacher dashboard navigation`
- `Update attendance filtering logic`
- `Improve responsive dashboard layout`
- `Add classroom management functionality`
- `Fix student profile validation`

## Pull Request Process

Before submitting your pull request:

- [ ] Ensure your code follows project conventions.
- [ ] Test your changes locally.
- [ ] Verify that existing features are not broken.
- [ ] Update documentation if necessary.
- [ ] Add screenshots for visual changes.
- [ ] Provide a clear pull request description.
- [ ] Link related issues when applicable.

Your pull request will be reviewed before it is merged. Changes may require updates based on feedback.

## Community Guidelines

All contributors are expected to:

- Be respectful and professional.
- Welcome constructive feedback.
- Help maintain a positive learning environment.
- Respect other contributors' work.
- Follow the project's Code of Conduct.

## Questions or Support

If you have questions, ideas, or need clarification, open an issue in the GitHub repository.

Thank you for helping make Attendify better! 💜

---

**Project Maintainer:** Hamna Shahid  
**Project:** Attendify — Student Attendance Management System  
**GitHub:** [@hamnashahiddev](https://github.com/hamnashahiddev)
