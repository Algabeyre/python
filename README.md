# Personal Budget Tracker (Flask)

A simple web app to track your income and expenses, built with Python Flask and SQLite.

## Features
- Add, view, edit, and delete income and expense entries
- Categorize transactions
- View summary: total income, total expenses, and balance

## Getting Started

### 1. Install dependencies
```
pip install flask flask_sqlalchemy
```

### 2. Run the app
```
python app.py
```

The app will be available at http://127.0.0.1:5000/

## Project Structure
- app.py: Main Flask application
- templates/: HTML templates (index.html, edit.html)
- budget.db: SQLite database (created automatically)

---

This project is for personal use and demo purposes. For production, add authentication and security features.
