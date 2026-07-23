# College Timetable Generator

A Flask web application that automates scheduling of courses, labs, and classrooms for college batches.

---

## What This Project Does

This is a **timetable management system** built with Python and Flask. It lets an admin:

1. **Create student batches** (e.g., "B.Tech 2024 CSE")
2. **Add classrooms and labs** (manually or via CSV upload)
3. **Schedule courses** into a weekly timetable grid (Mon-Fri, 8AM-5PM)
4. **Auto-assign rooms** — the system finds available classrooms/labs automatically
5. **Avoid conflicts** — prevents double-booking of professors and batches
6. **Export timetables** as Excel files (downloadable as ZIP)

---

## Features

- **Smart Scheduling** with multiple modes:
  - Regular (spread across different days)
  - 2-hour consecutive blocks
  - 2-1-1 pattern (2h + 1h + 1h on different days)
  - 2-1 pattern (2h + 1h)
  - Shift priority (morning or afternoon preference)
  - Day priority (prefer a specific day)
  - Avoid day (skip a specific day entirely)
- **Lunch Break** — Slot 4 (12:00-1:00 PM) is auto-blocked on all days
- **Conflict Detection** — No professor or batch double-booking
- **CSV Upload** — Bulk add classrooms/labs from CSV files
- **Excel Export** — Download timetables as `.xlsx` files
- **User Authentication** — Login system with hashed passwords
- **Bootstrap 5 UI** — Responsive design with modals and alerts

---

## Tech Stack

| Layer        | Technology                        |
| ------------ | --------------------------------- |
| Backend      | Python 3, Flask, Flask-SQLAlchemy |
| Database     | SQLite                            |
| Excel Export | openpyxl                          |
| Frontend     | Bootstrap 5, Font Awesome 6       |
| Auth         | Werkzeug password hashing         |

---

## Project Structure

```
timetable/
├── app.py              # Main application (routes, models, logic)
├── init_db.py          # Database initialization script
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── static/
│   └── mnnit.jpeg      # Logo image
├── templates/
│   ├── base.html           # Master layout template
│   ├── login.html          # Login page
│   ├── index.html          # Home page (batch listing)
│   ├── create_batch.html   # Create new batch form
│   ├── classrooms.html     # Classroom management
│   ├── labs.html           # Lab management
│   ├── manage_batch.html   # Timetable view + course scheduling
│   ├── select_batches.html # Download selection page
│   └── edit_schedule.html  # Move schedule entry form
├── instance/
│   └── timetable.db       # SQLite database (auto-created)
└── timetables/            # Temporary Excel files (auto-created)
```

---

## Installation

### 1. Clone / enter the project directory

```bash
cd timetable
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

The app will:

- Create the SQLite database automatically
- Create a default admin user (`admin` / `admin123`)
- Start at `http://127.0.0.1:5001`

---

## Usage

1. **Login** with `admin` / `admin123`
2. **Add Classrooms** — Go to Classrooms page, add rooms manually or upload CSV
3. **Add Labs** — Same process on the Labs page
4. **Create a Batch** — Click "New Batch" on the home page
5. **Schedule Courses** — Click "Manage" on a batch, fill in the course form
6. **View Timetable** — The grid updates after each scheduled course
7. **Download** — Select batches and download as Excel ZIP

### CSV Format for Classrooms/Labs

```csv
name,capacity
LH-101,60
LH-102,45
CS Lab 1,30
```

---

## How the Scheduling Algorithm Works

1. You specify: course name, credits, professor, and scheduling preferences
2. The system scans all 5 days × 9 slots to find available positions
3. It checks for conflicts (batch already has class, professor busy)
4. It skips the lunch slot (slot 4) and any "avoid day"
5. Based on the scheduling mode, it picks appropriate slots
6. It auto-assigns an available classroom or lab
7. Creates Schedule entries in the database
