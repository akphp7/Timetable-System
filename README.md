<h1 align="center">🗓️ Timetable System</h1>

<p align="center">
  A full-stack Flask web application that automates college course timetable generation with conflict-free scheduling, role-based access control, and Excel export.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-3.1.1-000000?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Database Design](#-database-design)
- [User Roles](#-user-roles)
- [Scheduling Algorithm](#-scheduling-algorithm)
- [Getting Started](#-getting-started)
- [Default Credentials](#-default-credentials)
- [Screenshots](#-screenshots)
- [API Routes](#-api-routes)

---

## 🔍 Overview

The **Timetable System** solves the complex problem of manually scheduling courses for multiple student batches across limited classrooms and labs. It ensures:

- ✅ No batch has two classes at the same time
- ✅ No professor is double-booked across batches
- ✅ No classroom or lab is assigned to two sessions simultaneously
- ✅ Lab sessions never span across the lunch break (12–1 PM)
- ✅ Slot 4 (12:00–1:00 PM) is always reserved for lunch

Built with **NIT Rourkela's** academic structure in mind — supporting CSE, ECE, EE, and ME departments across 3rd, 5th, and 7th semesters.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Auto-Scheduling** | Automatically finds conflict-free slots and assigns rooms |
| 🔒 **Role-Based Access** | Admin, Faculty, and Student roles with different permissions |
| 🧪 **Lab Support** | 2-hour consecutive slot handling for lab/practical sessions |
| 📅 **Priority Patterns** | Special scheduling modes: 2-hour, 2-1-1, 2-1, shift, day preference |
| 🚫 **Conflict Detection** | Prevents batch and professor double-booking in real time |
| 📤 **Excel Export** | Download timetables as `.xlsx` files, bundled in a ZIP |
| 📊 **Analytics Dashboard** | Classroom/lab utilization, professor workload charts (Chart.js) |
| 📁 **CSV Bulk Upload** | Add classrooms and labs in bulk via CSV file |
| ✏️ **Edit & Move Slots** | Manually move any scheduled entry to a different day/slot |
| 🗑️ **Clear Timetable** | Wipe a batch's entire schedule with one click |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.8+, Flask 3.1.1, Flask-SQLAlchemy 3.1.1 |
| **Database** | SQLite (via SQLAlchemy ORM) |
| **Authentication** | Session-based login, Werkzeug bcrypt password hashing |
| **Excel Export** | openpyxl 3.1.5 |
| **Frontend** | Bootstrap 5.3, Font Awesome 6.4, Jinja2 templating |
| **Charts** | Chart.js 4.4 (CDN) |

---

## 📁 Project Structure

```
timetable-rebuild/
│
├── app.py                  # Core: Flask app, DB models, scheduling logic, all routes (~1500 lines)
├── seed_data.py            # Populates DB with NIT Rourkela data & auto-generates timetables
├── init_db.py              # Standalone DB table creator
├── requirements.txt        # Python dependencies
│
├── static/
│   └── nitr.jpeg           # Institution logo
│
├── templates/
│   ├── base.html           # Master layout (navbar, flash messages)
│   ├── login.html          # Login page
│   ├── index.html          # Home — batch cards grid
│   ├── manage_batch.html   # Timetable grid + scheduling form (most complex)
│   ├── create_batch.html   # New batch form
│   ├── classrooms.html     # Manage classrooms (add/delete/CSV)
│   ├── labs.html           # Manage labs (add/delete/CSV)
│   ├── edit_schedule.html  # Move a schedule entry to a new slot
│   ├── select_batches.html # Select batches for Excel download
│   └── analytics.html      # Analytics dashboard with charts
│
└── instance/
    └── timetable.db        # SQLite database (auto-created, git-ignored)
```

---

## 🗄️ Database Design

The system has **7 tables** linked by foreign keys:

```
┌──────────┐    ┌──────────┐    ┌───────────┐
│   User   │    │  Batch   │    │  Course   │
│ id       │    │ id       │    │ id        │
│ username │    │ name     │    │ name      │
│ password │    └────┬─────┘    │ credits   │
│ role     │         │          │ is_lab    │
└──────────┘         │          └─────┬─────┘
                     │                │
              ┌──────▼────────────────▼──────────────────┐
              │                Schedule                   │
              │  id · batch_id · course_id · professor_id │
              │  day (0-4) · slot (0-8)                   │
              │  classroom_id (nullable)                  │
              │  lab_id (nullable)                        │
              └──────────────────────────────────────────┘
                     │                │
              ┌──────▼─────┐   ┌──────▼──────┐   ┌───────────┐
              │ Classroom  │   │    Lab      │   │ Professor │
              │ id · name  │   │ id · name   │   │ id · name │
              │ capacity   │   │ capacity    │   └───────────┘
              └────────────┘   └─────────────┘
```

**Key rule:** Each `Schedule` row = one time slot in one batch's weekly timetable.  
`day` is `0–4` (Mon–Fri), `slot` is `0–8` (8AM–5PM), slot `4` is always lunch.

---

## 👥 User Roles

### `admin` — Full Access
- Create, manage, and delete batches
- Schedule and edit courses for any batch
- Manage classrooms and labs (manual + CSV upload)
- Clear entire timetables
- Download Excel exports
- View analytics

### `faculty` — Read + Download
- View all batch timetables
- Download Excel exports
- View analytics dashboard

### `student` — Read + Download
- View all batch timetables
- Download Excel exports
- View analytics dashboard

---

## 🧠 Scheduling Algorithm

When a course is submitted via the scheduling form, the algorithm runs in one of **7 modes**:

| Mode | How It Works |
|---|---|
| **Default** | Finds one free slot per day, randomly picks N slots (N = credits) |
| **Lab** | Finds 2 consecutive free slots on the same day, assigns a lab room |
| **2-hour consecutive** | Like lab but in a classroom; places two 2-hour blocks on different days |
| **2-1-1** | 2 consecutive hours on Day 1, 1 hour on Day 2, 1 hour on Day 3 |
| **2-1** | 2 consecutive hours on Day 1, 1 hour on Day 2 |
| **Shift priority** | Restricts scheduling to morning (8AM–12PM) or afternoon (1PM–5PM) |
| **Day priority** | Prefers a specific day; uses afternoon slots for remaining days |

Additionally, an **Avoid Day** option tells the algorithm to skip a specific day entirely.

**Conflict checks before every placement:**
1. `Schedule.query.filter_by(batch_id, day, slot)` — batch free?
2. `Schedule.query.filter_by(professor_id, day, slot)` — professor free?
3. `Schedule.query.filter_by(classroom_id/lab_id, day, slot)` — room free?

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/akphp7/Timetable-System.git
cd Timetable-System

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / Mac
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed the database with NIT Rourkela data (creates users + sample timetables)
python seed_data.py

# 5. Run the app
python app.py
```

Open **http://127.0.0.1:5001** in your browser.

> **Note:** If you skip `seed_data.py`, the app still creates a default `admin/admin123` account — but you'll need to add classrooms, labs, and batches manually.

### Reset the Database

```bash
# Windows
del instance\timetable.db

# Linux / Mac
rm instance/timetable.db

python seed_data.py
```

---

## 🔑 Default Credentials

| Username | Password | Role | Access Level |
|---|---|---|---|
| `admin` | `admin123` | Admin | Full access |
| `faculty` | `faculty123` | Faculty | View + Download |
| `student` | `student123` | Student | View + Download |

> ⚠️ Change these credentials before deploying to production.

---

## 📊 Analytics Dashboard

The `/analytics` page shows:
- 📦 Summary counts (batches, classrooms, labs, courses, professors, scheduled slots)
- 📈 Classroom & lab utilization percentage bars
- 📊 Bar chart — classes per day (Mon–Fri)
- 📊 Bar chart — classes per time slot (8AM–5PM)
- 📊 Horizontal bar — professor workload (hours/week, sorted)
- 📊 Horizontal bar — courses per batch

---

## 📤 Excel Export

1. Go to **Download** in the navbar
2. Select one or more batches
3. Click **Download** — receives a `timetables.zip` containing one `.xlsx` per batch

Each Excel file has:
- **Row 1:** Batch name title (merged)
- **Row 2:** Time slot headers (8AM–5PM)
- **Rows 3–7:** Monday to Friday, each cell showing `Course (Professor) [Lab] {Room}`

---

## 📡 API Routes

| Method | URL | Auth | Description |
|---|---|---|---|
| GET/POST | `/login` | — | Login page |
| GET | `/logout` | Any | Logout |
| GET | `/` | Any | Home — batch list |
| GET/POST | `/create_batch` | Admin | Create a new batch |
| POST | `/batch/<id>/delete` | Admin | Delete batch + schedules |
| GET/POST | `/batch/<id>` | Any | View/manage timetable |
| POST | `/batch/<id>/clear` | Admin | Clear all schedules |
| POST | `/schedule/<id>/delete` | Admin | Remove one slot |
| GET/POST | `/schedule/<id>/edit` | Admin | Move slot to new day/time |
| GET/POST | `/classrooms` | Admin | Manage classrooms |
| POST | `/classrooms/<id>/delete` | Admin | Delete classroom |
| GET/POST | `/labs` | Admin | Manage labs |
| POST | `/labs/<id>/delete` | Admin | Delete lab |
| GET | `/select_batches` | Any | Batch selection for download |
| POST | `/download-timetable` | Any | Generate & download ZIP |
| GET | `/analytics` | Any | Analytics dashboard |

---

## 📜 CSV Format

For bulk importing classrooms or labs:

```csv
name,capacity
LA-101,120
LA-102,60
CSE Lab-1,40
```

Upload via the **Classrooms** or **Labs** management pages.

---

<p align="center">Built with ❤️ for NIT Rourkela · Flask + SQLAlchemy + Bootstrap 5</p>
