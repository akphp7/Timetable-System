# Timetable System — Complete Project Documentation

> **Prepared for:** Interview / Technical Discussion  
> **Project Location:** `e:\NIT_PROJECTS\timetable-rebuild`  
> **Stack:** Python · Flask · SQLAlchemy · SQLite · Jinja2 · Bootstrap 5 · Chart.js

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack & Libraries](#2-tech-stack--libraries)
3. [Architecture & Project Structure](#3-architecture--project-structure)
4. [Database Design (Models)](#4-database-design-models)
5. [Authentication & Role-Based Access Control](#5-authentication--role-based-access-control)
6. [Role Breakdown — What Each Role Can Do](#6-role-breakdown--what-each-role-can-do)
7. [Scheduling Algorithm — How It Works](#7-scheduling-algorithm--how-it-works)
8. [All Routes / Endpoints](#8-all-routes--endpoints)
9. [Template System](#9-template-system)
10. [Analytics Dashboard](#10-analytics-dashboard)
11. [Excel Export & Download](#11-excel-export--download)
12. [Seed Data (NIT Rourkela Dataset)](#12-seed-data-nit-rourkela-dataset)
13. [Running the Project](#13-running-the-project)
14. [Common Interview Questions & Answers](#14-common-interview-questions--answers)

---

## 1. Project Overview

The **Timetable System** is a full-stack web application built with **Flask (Python)** that automates the generation and management of college course timetables. It was designed with NIT Rourkela's academic structure in mind.

### Core Problem It Solves
Manually scheduling timetables for dozens of batches, hundreds of courses, and multiple professors across limited classrooms and labs is error-prone and time-consuming. This system:
- Automatically finds available time slots while **avoiding conflicts**
- Ensures no batch and no professor is double-booked at the same time
- Supports **special scheduling patterns** (lab courses, priority courses)
- Exports timetables to **Excel** for distribution
- Provides an **analytics dashboard** to monitor utilization

### Key Capabilities
| Feature | Description |
|---|---|
| Auto-scheduling | Assigns courses to free slots automatically |
| Conflict detection | Prevents double-booking of batches and professors |
| Role-based access | Admin, Faculty, Student have different permissions |
| Excel export | Download timetables as `.xlsx` files zipped together |
| Analytics | Charts for classroom/lab utilization, professor workload |
| Lab support | 2-hour consecutive slot handling for lab courses |
| Priority patterns | Special slot arrangements (2-hour, 2-1-1, 2-1) |

---

## 2. Tech Stack & Libraries

| Library | Version | Purpose |
|---|---|---|
| **Flask** | 3.1.1 | Web framework — routing, templating, sessions |
| **Flask-SQLAlchemy** | 3.1.1 | ORM — Python classes as database tables |
| **SQLite** | built-in | File-based relational database (`instance/timetable.db`) |
| **openpyxl** | 3.1.5 | Generate Excel `.xlsx` files |
| **Werkzeug** | ≥3.0.0 | Password hashing (`generate_password_hash`, `check_password_hash`) |
| **pypdf** | 4.3.1 | PDF extraction (for research paper module) |
| **scikit-learn** | 1.5.1 | TF-IDF vectorization (for paper mentor module) |
| **Bootstrap 5** | 5.3.0 | Responsive CSS framework (CDN) |
| **Font Awesome** | 6.4.0 | Icon library (CDN) |
| **Chart.js** | 4.4.0 | Analytics charts (CDN) |
| **Jinja2** | built-in with Flask | HTML template engine |

---

## 3. Architecture & Project Structure

```
timetable-rebuild/
│
├── app.py                  ← THE MAIN FILE: Flask app, DB models, all routes (1498 lines)
├── init_db.py              ← Standalone DB initializer (creates tables)
├── seed_data.py            ← Populates DB with NIT Rourkela data + generates timetables
├── requirements.txt        ← Python package dependencies
│
├── static/
│   └── nitr.jpeg           ← Institution logo (used in navbar and login page)
│
├── templates/              ← Jinja2 HTML templates
│   ├── base.html           ← Master layout (navbar, flash messages, footer)
│   ├── login.html          ← Login page
│   ├── index.html          ← Home page (batch cards)
│   ├── manage_batch.html   ← Timetable view + scheduling form (most complex page)
│   ├── create_batch.html   ← Form to create a new batch
│   ├── classrooms.html     ← Manage classrooms (add/delete/CSV upload)
│   ├── labs.html           ← Manage labs (add/delete/CSV upload)
│   ├── edit_schedule.html  ← Move a schedule entry to different slot
│   ├── select_batches.html ← Choose batches to download as Excel
│   └── analytics.html      ← Analytics dashboard with Chart.js charts
│
├── instance/
│   └── timetable.db        ← SQLite database file (auto-created)
│
├── timetables/             ← Temp folder for generated Excel files (auto-cleaned)
├── knowledge_engine/       ← (separate module) research paper knowledge engine
└── paper_mentor/           ← (separate module) paper recommendation engine
```

### Request-Response Flow
```
Browser → HTTP Request
    → Flask Router (app.py @app.route)
        → Decorator check (@login_required / @role_required)
            → Route function runs business logic
                → SQLAlchemy queries the SQLite DB
                    → render_template() fills Jinja2 HTML
                        → HTML Response → Browser
```

---

## 4. Database Design (Models)

There are **7 database tables** defined as Python classes in `app.py`.

### Entity Relationship Overview
```
User          (login accounts with roles)
Batch         (group of students, e.g. CSE5A)
Course        (subject with credit hours, e.g. Data Structures)
Professor     (faculty member teaching a course)
Classroom     (lecture hall with capacity)
Lab           (computer/science lab with capacity)
Schedule      (THE CORE TABLE — links everything together)
```

---

### `User`
Stores login credentials and roles.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `username` | String(50), unique | Login username |
| `password_hash` | String(256) | bcrypt-hashed password (never plain text) |
| `role` | String(20) | `admin`, `faculty`, or `student` |

**Methods:**
- `set_password(password)` — hashes and stores the password
- `check_password(password)` — verifies login password against hash

---

### `Batch`
A group of students that shares a single timetable.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(50), unique | e.g. `CSE5A`, `ECE3B` |

---

### `Course`
A subject that needs to be scheduled.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(50), unique | e.g. `Data Structures` |
| `credits` | Integer | Hours per week (1–4) |
| `is_lab` | Boolean | True = lab course (2 consecutive hours) |
| `priority` | Boolean | True = uses a special scheduling pattern |

---

### `Professor`
A faculty member. Tracked to prevent double-booking.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(50), unique | e.g. `Dr. Santosh Kumar Pani` |

---

### `Classroom`
A lecture hall for regular classes.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(50), unique | e.g. `LA-101`, `LH-202` |
| `capacity` | Integer | Max students (e.g. 60, 120) |

---

### `Lab`
A computer or science lab for practical sessions.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(50), unique | e.g. `CSE Lab-1 (Programming)` |
| `capacity` | Integer | Max students |

---

### `Schedule` ← **The Core Table**
Every row = one time slot in one batch's weekly timetable.

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `batch_id` | FK → Batch | Which batch |
| `course_id` | FK → Course | Which course |
| `professor_id` | FK → Professor | Who teaches it |
| `day` | Integer (0–4) | 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri |
| `slot` | Integer (0–8) | 0=8AM-9AM … 8=4PM-5PM (slot 4 = lunch) |
| `classroom_id` | FK → Classroom (nullable) | Room assigned (null for labs) |
| `lab_id` | FK → Lab (nullable) | Lab assigned (null for lectures) |

**Example row:** Batch CSE5A has Data Structures with Dr. Smith on Monday (day=0) at slot 1 (9-10AM) in classroom LA-101.

---

## 5. Authentication & Role-Based Access Control

### Session-Based Login
Flask uses **signed browser cookies** (sessions) to remember logged-in users.

```python
session['user_id']   = user.id       # Stored on login
session['username']  = user.username
session['role']      = user.role     # 'admin', 'faculty', or 'student'
```

### Two Custom Decorators

#### `@login_required`
Protects any route from unauthenticated access.
```python
@app.route('/some-page')
@login_required
def some_page():
    ...   # Only runs if user is logged in
```
If not logged in → redirected to `/login?next=<original-url>` so they return after login.

#### `@role_required(*roles)`
Protects routes from users without the required role.
```python
@app.route('/classrooms', methods=['GET', 'POST'])
@role_required('admin')        # Only admins can access
def manage_classrooms():
    ...
```
You can pass multiple roles: `@role_required('admin', 'faculty')`.

### Open Redirect Protection
After login, the `next` URL is validated using `is_safe_redirect_url()` which checks that the URL points to the **same host** — preventing attackers from crafting a link like `/login?next=https://evil.com`.

---

## 6. Role Breakdown — What Each Role Can Do

### `admin` (Full Access)

| Page / Feature | Access |
|---|---|
| Home — view all batches | ✅ |
| Create new batch | ✅ |
| Delete a batch (and all its schedules) | ✅ |
| View batch timetable grid | ✅ |
| Schedule a new course for a batch | ✅ |
| Edit a schedule entry (move to different slot) | ✅ |
| Delete individual schedule entries | ✅ |
| Clear entire timetable for a batch | ✅ |
| Manage classrooms (add/delete/CSV upload) | ✅ |
| Manage labs (add/delete/CSV upload) | ✅ |
| Download timetables as Excel/ZIP | ✅ |
| Analytics dashboard | ✅ |

**Default credentials:** `admin` / `admin123`

---

### `faculty` (Read + Download)

| Page / Feature | Access |
|---|---|
| Home — view all batches | ✅ |
| View batch timetable grid | ✅ (view only, no form shown) |
| Download timetables as Excel/ZIP | ✅ |
| Analytics dashboard | ✅ |
| Create/delete batches | ❌ |
| Schedule courses | ❌ |
| Edit/delete schedule entries | ❌ |
| Manage classrooms or labs | ❌ |

**Default credentials:** `faculty` / `faculty123`

---

### `student` (Read + Download)

| Page / Feature | Access |
|---|---|
| Home — view all batches | ✅ |
| View batch timetable grid | ✅ (view only) |
| Download timetables as Excel/ZIP | ✅ |
| Analytics dashboard | ✅ |
| All administrative functions | ❌ |

**Default credentials:** `student` / `student123`

---

### Role Comparison Summary

| Feature | Admin | Faculty | Student |
|---|:---:|:---:|:---:|
| View timetables | ✅ | ✅ | ✅ |
| Download Excel | ✅ | ✅ | ✅ |
| Analytics | ✅ | ✅ | ✅ |
| Schedule courses | ✅ | ❌ | ❌ |
| Manage classrooms/labs | ✅ | ❌ | ❌ |
| Create/delete batches | ✅ | ❌ | ❌ |
| Edit/delete schedules | ✅ | ❌ | ❌ |

---

## 7. Scheduling Algorithm — How It Works

This is the **core intelligence** of the system, implemented in the `manage_batch()` route.

### Time Slot Mapping
```
Slot 0  →  08:00 AM – 09:00 AM
Slot 1  →  09:00 AM – 10:00 AM
Slot 2  →  10:00 AM – 11:00 AM
Slot 3  →  11:00 AM – 12:00 PM
Slot 4  →  12:00 PM – 01:00 PM  ← LUNCH (always blocked)
Slot 5  →  01:00 PM – 02:00 PM
Slot 6  →  02:00 PM – 03:00 PM
Slot 7  →  03:00 PM – 04:00 PM
Slot 8  →  04:00 PM – 05:00 PM
```

### Helper Functions

#### `is_slot_available(batch_id, professor_id, day, slot, is_lab=False)`
A slot is **unavailable** if:
1. The batch already has a class at that day+slot
2. The professor is already teaching another batch at that day+slot

For lab courses it checks **two consecutive slots** (slot and slot+1).

#### `find_available_classroom(day, slot)`
Loops through all classrooms, returns the first one with no existing booking at that day+slot.

#### `find_available_lab(day, slot)`
Loops through all labs, returns the first one free for **both** `slot` and `slot+1`.

---

### Scheduling Modes

When an admin submits the "Schedule a Course" form, the algorithm runs in one of **7 modes**:

---

#### Mode A — Default (Regular Course)
- Finds one free slot per day across Mon–Fri
- Randomly picks `N` slots where `N = credits` of the course
- Places one class per day (no two sessions same day)
- Assigns a free classroom to each

**Example:** Data Structures, 3 credits → Monday slot 2, Wednesday slot 6, Friday slot 1

---

#### Mode B — Lab Course (`is_lab = True`)
- Looks for days where **2 consecutive slots** are free for both the batch AND the professor
- Skips slot 3 (11-12) and 4 (12-13) because a lab can't span over lunch
- Randomly picks one valid day
- Assigns a **lab room** (not a classroom) for both slots

**Example:** DS Lab, 2 credits → Tuesday slots 5+6 (1-2PM, 2-3PM) in CSE Lab-1

---

#### Mode C — Priority: 2-hour Consecutive
- Like a lab but uses a **classroom** (not a lab room)
- Finds days where 2 consecutive classroom slots are free
- Places **two** 2-hour blocks on two different days
- Good for courses that need longer, uninterrupted sessions

---

#### Mode D — Priority: 2-1-1
- Designed for **4-credit courses**
- Day 1: Places 2 consecutive hours
- Day 2: Places 1 hour
- Day 3: Places 1 hour
- Total = 4 hours per week

**Example:** Design & Analysis of Algorithms (4 cr) → Mon 9-11AM, Wed 2-3PM, Thu 3-4PM

---

#### Mode E — Priority: 2-1
- Designed for **3-credit courses** that need a concentrated session
- Day 1: Places 2 consecutive hours
- Day 2: Places 1 hour
- Total = 3 hours per week

---

#### Mode F — Priority Shift
- Forces the course to be scheduled only in:
  - **First half** (morning): slots 0–3 (8AM–12PM)
  - **Second half** (afternoon): slots 5–8 (1PM–5PM)
- Useful when a professor or batch has morning/afternoon preferences

---

#### Mode G — Priority Day
- Tries to place the course on a **preferred day** first
- If preferred day has a slot → places it there
- For other days, only looks at **afternoon slots** (5–8)
- Useful when a professor is only available on certain days

---

### Avoid Day Feature
For any scheduling mode, you can select a day to **avoid**. The algorithm simply skips that day during its slot search. Useful when a professor has commitments on a specific day.

---

### Conflict Prevention Summary
The system guarantees:
1. ✅ No batch has two classes at the same day+slot
2. ✅ No professor teaches two batches at the same day+slot
3. ✅ No classroom is used by two different classes simultaneously
4. ✅ No lab is used by two batches simultaneously
5. ✅ Lab sessions never span across the lunch break
6. ✅ Slot 4 (12–1 PM) is always reserved for lunch

---

## 8. All Routes / Endpoints

| Method | URL | Function | Auth Required | Description |
|---|---|---|---|---|
| GET/POST | `/login` | `login()` | None | Login page and form processing |
| GET | `/logout` | `logout()` | None | Clears session, redirects to login |
| GET | `/` | `index()` | `login_required` | Home page — all batches as cards |
| GET/POST | `/create_batch` | `create_batch()` | `admin` | Form to create a new batch |
| POST | `/batch/<id>/delete` | `delete_batch()` | `admin` | Deletes batch + all its schedules |
| GET/POST | `/batch/<id>` | `manage_batch()` | `login_required` | View timetable grid + schedule form (admin only for POST) |
| POST | `/batch/<id>/clear` | `clear_batch_timetable()` | `admin` | Wipes all schedules for a batch |
| POST | `/schedule/<id>/delete` | `delete_schedule()` | `admin` | Removes one schedule entry |
| GET/POST | `/schedule/<id>/edit` | `edit_schedule()` | `admin` | Move schedule entry to new day/slot |
| GET/POST | `/classrooms` | `manage_classrooms()` | `admin` | View, add (manual or CSV), delete classrooms |
| POST | `/classrooms/<id>/delete` | `delete_classroom()` | `admin` | Deletes a classroom |
| GET/POST | `/labs` | `manage_labs()` | `admin` | View, add (manual or CSV), delete labs |
| POST | `/labs/<id>/delete` | `delete_lab()` | `admin` | Deletes a lab |
| GET | `/select_batches` | `select_batches()` | `login_required` | Select batches for Excel download |
| POST | `/download-timetable` | `download_timetable()` | `login_required` | Generate and download ZIP of Excel files |
| GET | `/analytics` | `analytics()` | `login_required` | Analytics dashboard with charts |

**Total: 16 routes**

---

## 9. Template System

All templates use **Jinja2 template inheritance** — they extend `base.html` to avoid code duplication.

### `base.html` — Master Layout
- Defines the shared structure for all pages
- Contains: `<head>` (CSS, meta), navbar, flash message renderer, Bootstrap JS
- Defines three **blocks** that child templates override:
  - `{% block title %}` — Page title in browser tab
  - `{% block content %}` — Main page body
  - `{% block extra_css %}` / `{% block extra_js %}` — Page-specific CSS/JS

### Navbar (in `base.html`)
- Displays the **NITR logo** (`nitr.jpeg`) as a circular 40×40px image
- Shows nav links only when the user **is logged in** (`session.get('user_id')`)
- Shows **Classrooms** and **Labs** links only for `admin` role
- Right side: username + role badge + Logout button

### Flash Messages
Flask's `flash()` function queues one-time messages (shown once, then gone).
Categories map to Bootstrap alert colors:
- `success` → green ✅
- `error` → red ❌
- `warning` → yellow ⚠️
- `info` → blue ℹ️

### `manage_batch.html` — Most Complex Template
Has three sections:
1. **Course Scheduling Form** (admin only, hidden from others)
   - Inputs: Course Name, Credits, Professor Name, Avoid Day
   - Checkboxes: Lab Course, Priority Course, Priority Day, Priority Shift
   - Conditional dropdowns revealed by JavaScript `onchange` handlers
2. **Timetable Grid** — 5×9 HTML table (days × slots)
3. **Scheduled Entries List** — Detailed table with Edit + Delete buttons per entry

---

## 10. Analytics Dashboard

The `/analytics` route computes and sends these data points to `analytics.html`:

| Metric | How Computed |
|---|---|
| **Total counts** | `Batch.query.count()`, etc. for each model |
| **Classroom utilization %** | `used_classroom_slots / (classrooms × 5 days × 8 usable slots) × 100` |
| **Lab utilization %** | Same formula for labs |
| **Per-classroom usage** | `Schedule.query.filter_by(classroom_id=cr.id).count()` |
| **Per-lab usage** | `Schedule.query.filter_by(lab_id=lb.id).count()` |
| **Professor workload** | `Schedule.query.filter_by(professor_id=prof.id).count()` (total hours/week) |
| **Courses per batch** | Distinct course IDs scheduled per batch |
| **Day distribution** | Count of all schedule entries per day (0–4) |
| **Slot distribution** | Count of all schedule entries per slot (0–8) |

### Charts (Chart.js)
| Chart | Type | Shows |
|---|---|---|
| Classes per Day | Bar chart | Which days have most classes |
| Classes per Time Slot | Bar chart | Which hours are busiest |
| Professor Workload | Horizontal bar | Hours/week per professor (sorted descending) |
| Courses per Batch | Horizontal bar | Number of distinct courses per batch |

---

## 11. Excel Export & Download

### Flow
1. User visits `/select_batches` → sees checkboxes for all batches
2. Selects desired batches → submits form (POST to `/download-timetable`)
3. For each selected batch, `generate_excel([batch_id])` is called
4. Each Excel file is added to a **ZIP archive in memory** (using `BytesIO`)
5. ZIP is sent as a file download (`timetables.zip`)
6. Temporary `.xlsx` files are **immediately deleted** after adding to ZIP

### Excel File Structure (`generate_excel()`)
- **Row 1:** Title — "Timetable for Batch: CSE5A" (merged across all columns)
- **Row 2:** Headers — Day | 08:00-09:00 | 09:00-10:00 | … | 16:00-17:00
- **Rows 3-7:** Monday through Friday, each slot filled with:  
  `CourseName (ProfName) [LabName] {RoomName}`

---

## 12. Seed Data (NIT Rourkela Dataset)

Running `python seed_data.py` populates the database with realistic NIT Rourkela data:

### What Gets Created
| Item | Count |
|---|---|
| Classrooms | 16 (LA-101 to SA-202, capacities 60–120) |
| Labs | 11 (CSE, ECE, EE, ME labs, capacities 30–40) |
| Batches | 21 (CSE, ECE, EE, ME — 3rd, 5th, 7th semesters) |
| Users | 3 (admin, faculty, student) |

### Batches
`CSE3A`, `CSE3B`, `CSE5A`, `CSE5B`, `CSE7A`, `CSE7B`,  
`ECE3A`, `ECE3B`, `ECE5A`, `ECE5B`, `ECE7A`, `ECE7B`,  
`EE3A`, `EE5A`, `EE7A`,  
`ME3A`, `ME3B`, `ME5A`, `ME5B`, `ME7A`, `ME7B`

### Seed Algorithm
For each batch's courses, the seed script:
1. Creates the Course and Professor (or reuses if existing)
2. Shuffles the days randomly
3. Finds valid slots using the same `is_slot_available()` and `find_available_lab()` helpers
4. Creates Schedule entries in the database

---

## 13. Running the Project

### Prerequisites
- Python 3.8+
- All dependencies installed (see `requirements.txt`)

### Setup & Start

```powershell
# Step 1: Navigate to project
cd e:\NIT_PROJECTS\timetable-rebuild

# Step 2: Activate virtual environment (already exists)
.\venv\Scripts\activate

# Step 3: Install dependencies (first time only)
pip install -r requirements.txt

# Step 4: Seed the database with NIT Rourkela data (first time only)
python seed_data.py

# Step 5: Run the app
python app.py
```

Open **http://127.0.0.1:5001** in your browser.

### Login Credentials
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Full access |
| `faculty` | `faculty123` | Read + download |
| `student` | `student123` | Read + download |

### Reset the Database
```powershell
del instance\timetable.db   # Delete old DB
python seed_data.py          # Re-create and re-seed
```

---

## 14. Common Interview Questions & Answers

---

**Q: What is Flask and why did you use it?**  
A: Flask is a lightweight Python web framework. It handles HTTP routing, template rendering, and session management. I chose it because it's minimal and unopinionated — I have full control over the architecture without the overhead of Django.

---

**Q: What is an ORM? Why use SQLAlchemy?**  
A: An ORM (Object-Relational Mapper) lets you interact with a database using Python classes instead of writing raw SQL. `Course.query.filter_by(name="Data Structures").first()` is equivalent to `SELECT * FROM course WHERE name = 'Data Structures' LIMIT 1`. It makes the code cleaner, more Pythonic, and database-agnostic.

---

**Q: How does the scheduling algorithm prevent conflicts?**  
A: Before placing any course, `is_slot_available()` queries the Schedule table twice:
1. **Batch conflict check:** `Schedule.query.filter_by(batch_id=..., day=..., slot=...)` — ensures the batch has no class at that time.
2. **Professor conflict check:** `Schedule.query.filter_by(professor_id=..., day=..., slot=...)` — ensures the professor isn't teaching another batch simultaneously.
Only if both return `None` (no conflict found) is the slot considered available.

---

**Q: How does template inheritance work?**  
A: `base.html` defines the page skeleton with named `{% block %}` tags. Child templates use `{% extends 'base.html' %}` and override those blocks. Anything outside a block in `base.html` appears on every page — like the navbar and flash messages. This eliminates code duplication across 10 templates.

---

**Q: How are passwords stored securely?**  
A: Passwords are **never stored in plain text**. When a user is created, `set_password()` calls Werkzeug's `generate_password_hash()` which applies bcrypt hashing. At login, `check_password_hash()` compares the submitted password against the stored hash. Even if the database is compromised, attackers cannot recover the original passwords.

---

**Q: What is the `@login_required` decorator and how does it work?**  
A: It's a Python decorator that wraps route functions. Using `functools.wraps`, it creates a wrapper function that first checks `session['user_id']`. If the key doesn't exist (not logged in), it redirects to the login page. If it exists, the original route function is called normally. The `next` parameter is appended to remember where the user was going.

---

**Q: How does the Excel export work?**  
A: The `generate_excel()` function builds a 5×9 Python list (days × slots) by querying Schedule entries, then uses `openpyxl` to create a formatted Excel file. For downloads, multiple Excel files are packed into a **ZIP archive held in memory** (`BytesIO`) — no files are stored permanently on the server. Flask's `send_file()` streams the ZIP to the browser.

---

**Q: What's the difference between a classroom and a lab in this system?**  
A: Both are physical rooms, but they're used differently. **Classrooms** host regular 1-hour lecture sessions. **Labs** host practical sessions that occupy **2 consecutive time slots**. The database tracks them separately, and the scheduling algorithm uses `find_available_lab()` which checks two slots simultaneously, while `find_available_classroom()` checks only one slot.

---

**Q: How does the analytics page work?**  
A: The `/analytics` route performs 7 separate calculations using SQLAlchemy aggregate queries (`.count()`, `.distinct()`) and sends all data to the template. The template uses **Chart.js** (loaded via CDN) to render 4 interactive charts: bar charts for day/slot distribution, and horizontal bar charts for professor workload and courses per batch.

---

**Q: What happens if two admins try to schedule the same slot simultaneously?**  
A: SQLite handles concurrent writes using file-level locking. The first write succeeds; the second would detect the conflict only when its own `is_slot_available()` check runs — but since both happen in separate requests, there's a small race condition window. For a production system, this would be addressed with database-level transactions and row locks.

---

**Q: How would you improve this project?**  
A: Several areas for improvement:
1. **Database:** Switch from SQLite to PostgreSQL for production use
2. **Scheduler:** Implement a proper constraint satisfaction or backtracking algorithm for optimal slot distribution
3. **CSRF protection:** Add Flask-WTF CSRF tokens to all POST forms
4. **API:** Add a REST API layer so the frontend could be a React/Vue SPA
5. **Auto-generation:** One-click "generate full timetable for all batches" button
6. **Notifications:** Email professors their weekly schedule
7. **Conflict report:** Show a report of unscheduled courses when slots run out

---

*Documentation prepared for: NIT Rourkela Timetable System — July 2026*
