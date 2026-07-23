"""
seed_data.py — Populates the database with NIT Rourkela-style data.

This script adds:
- Classrooms (Lecture Halls used at NIT Rourkela)
- Labs (Computer labs, Electronics labs, etc.)
- Batches (CSE, ECE, EE, ME sections for 3rd, 5th, 7th semester)
- Courses with professors assigned to each batch
- Auto-generates timetables using the app's scheduling algorithm

Run this once:  python seed_data.py
"""

import sys
import os
import random

# Add the project directory so we can import app
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Classroom, Lab, Batch, Course, Professor, Schedule, User
from app import find_available_classroom, find_available_lab, is_slot_available

# ============================================================================
# NIT ROURKELA INFRASTRUCTURE
# ============================================================================

CLASSROOMS = [
    # Lecture Halls at NIT Rourkela
    ("LA-101", 120), ("LA-102", 120), ("LA-103", 60),
    ("LA-104", 60),  ("LA-201", 120), ("LA-202", 120),
    ("LA-203", 60),  ("LA-204", 60),
    ("LH-101", 90),  ("LH-102", 90),
    ("LH-201", 90),  ("LH-202", 90),
    ("SA-101", 60),  ("SA-102", 60),
    ("SA-201", 60),  ("SA-202", 60),
]

LABS = [
    # Computer Science / IT Labs
    ("CSE Lab-1 (Programming)", 40),
    ("CSE Lab-2 (Networks)", 40),
    ("CSE Lab-3 (OS/Systems)", 40),
    ("CSE Lab-4 (AI/ML)", 40),
    # Electronics Labs
    ("ECE Lab-1 (Digital)", 35),
    ("ECE Lab-2 (Analog)", 35),
    ("ECE Lab-3 (Communication)", 35),
    # Electrical Labs
    ("EE Lab-1 (Machines)", 35),
    ("EE Lab-2 (Power Systems)", 35),
    # Mechanical Labs
    ("ME Lab-1 (Thermal)", 30),
    ("ME Lab-2 (Manufacturing)", 30),
]

# ============================================================================
# NIT ROURKELA BATCHES
# ============================================================================
# Convention: <Dept><Semester><Section>
# Example: CSE5A = Computer Science, 5th Semester, Section A

BATCHES = [
    # CSE — 2 sections per semester
    "CSE3A", "CSE3B",
    "CSE5A", "CSE5B",
    "CSE7A", "CSE7B",
    # ECE — 2 sections
    "ECE3A", "ECE3B",
    "ECE5A", "ECE5B",
    "ECE7A", "ECE7B",
    # EE — 1 section each
    "EE3A", "EE5A", "EE7A",
    # ME — 2 sections
    "ME3A", "ME3B",
    "ME5A", "ME5B",
    "ME7A", "ME7B",
]

# ============================================================================
# NIT ROURKELA COURSES & PROFESSORS (by batch)
# ============================================================================
# Each entry: (course_name, credits, is_lab, professor_name)
#
# Courses are realistic NIT Rourkela CSE/ECE/EE/ME curriculum.
# Professor names are fictional but styled realistically.

BATCH_COURSES = {
    # ----- CSE 3rd Semester -----
    "CSE3A": [
        ("Data Structures", 3, False, "Dr. Santosh Kumar Pani"),
        ("Discrete Mathematics", 3, False, "Dr. Pankaj Kumar Sa"),
        ("Digital Logic Design", 3, False, "Dr. Bibhudatta Sahoo"),
        ("Object Oriented Programming", 3, False, "Dr. Sanjay Kumar Jena"),
        ("Data Structures Lab", 2, True, "Dr. Santosh Kumar Pani"),
        ("OOP Lab", 2, True, "Dr. Sanjay Kumar Jena"),
        ("Probability & Statistics", 3, False, "Dr. Manas Ranjan Tripathy"),
    ],
    "CSE3B": [
        ("Data Structures", 3, False, "Dr. Ratnakar Dash"),
        ("Discrete Mathematics", 3, False, "Dr. Pankaj Kumar Sa"),
        ("Digital Logic Design", 3, False, "Dr. Bibhudatta Sahoo"),
        ("Object Oriented Programming", 3, False, "Dr. Durga Prasad Mohapatra"),
        ("Data Structures Lab", 2, True, "Dr. Ratnakar Dash"),
        ("OOP Lab", 2, True, "Dr. Durga Prasad Mohapatra"),
        ("Probability & Statistics", 3, False, "Dr. Manas Ranjan Tripathy"),
    ],

    # ----- CSE 5th Semester -----
    "CSE5A": [
        ("Design & Analysis of Algorithms", 3, False, "Dr. Bansidhar Majhi"),
        ("Operating Systems", 3, False, "Dr. Pankaj Kumar Sa"),
        ("Database Management Systems", 3, False, "Dr. Sanjay Kumar Jena"),
        ("Computer Networks", 3, False, "Dr. Santos Kumar Das"),
        ("OS Lab", 2, True, "Dr. Pankaj Kumar Sa"),
        ("DBMS Lab", 2, True, "Dr. Sanjay Kumar Jena"),
        ("Formal Language & Automata Theory", 3, False, "Dr. Santosh Kumar Pani"),
    ],
    "CSE5B": [
        ("Design & Analysis of Algorithms", 3, False, "Dr. Bansidhar Majhi"),
        ("Operating Systems", 3, False, "Dr. Ratnakar Dash"),
        ("Database Management Systems", 3, False, "Dr. Sanjay Kumar Jena"),
        ("Computer Networks", 3, False, "Dr. Santos Kumar Das"),
        ("OS Lab", 2, True, "Dr. Ratnakar Dash"),
        ("DBMS Lab", 2, True, "Dr. Sanjay Kumar Jena"),
        ("Formal Language & Automata Theory", 3, False, "Dr. Santosh Kumar Pani"),
    ],

    # ----- CSE 7th Semester -----
    "CSE7A": [
        ("Machine Learning", 3, False, "Dr. Pankaj Kumar Sa"),
        ("Compiler Design", 3, False, "Dr. Durga Prasad Mohapatra"),
        ("Information Security", 3, False, "Dr. Santos Kumar Das"),
        ("Distributed Systems", 3, False, "Dr. Sanjay Kumar Jena"),
        ("ML Lab", 2, True, "Dr. Pankaj Kumar Sa"),
        ("Elective: NLP", 3, False, "Dr. Bansidhar Majhi"),
    ],
    "CSE7B": [
        ("Machine Learning", 3, False, "Dr. Ratnakar Dash"),
        ("Compiler Design", 3, False, "Dr. Durga Prasad Mohapatra"),
        ("Information Security", 3, False, "Dr. Santos Kumar Das"),
        ("Distributed Systems", 3, False, "Dr. Bibhudatta Sahoo"),
        ("ML Lab", 2, True, "Dr. Ratnakar Dash"),
        ("Elective: Cloud Computing", 3, False, "Dr. Sanjay Kumar Jena"),
    ],

    # ----- ECE 3rd Semester -----
    "ECE3A": [
        ("Signals & Systems", 3, False, "Dr. Sukadev Meher"),
        ("Electronic Devices & Circuits", 3, False, "Dr. Kamalakanta Mahapatra"),
        ("Network Theory", 3, False, "Dr. Umesh Chandra Pati"),
        ("Digital System Design", 3, False, "Dr. Samit Ari"),
        ("EDC Lab", 2, True, "Dr. Kamalakanta Mahapatra"),
        ("Engineering Mathematics-III", 3, False, "Dr. Manas Ranjan Tripathy"),
    ],
    "ECE3B": [
        ("Signals & Systems", 3, False, "Dr. Sukadev Meher"),
        ("Electronic Devices & Circuits", 3, False, "Dr. Kamalakanta Mahapatra"),
        ("Network Theory", 3, False, "Dr. Umesh Chandra Pati"),
        ("Digital System Design", 3, False, "Dr. Samit Ari"),
        ("EDC Lab", 2, True, "Dr. Kamalakanta Mahapatra"),
        ("Engineering Mathematics-III", 3, False, "Dr. Manas Ranjan Tripathy"),
    ],

    # ----- ECE 5th Semester -----
    "ECE5A": [
        ("Digital Communication", 3, False, "Dr. Sukadev Meher"),
        ("Microprocessors & Microcontrollers", 3, False, "Dr. Samit Ari"),
        ("Control Systems", 3, False, "Dr. Umesh Chandra Pati"),
        ("Electromagnetic Theory", 3, False, "Dr. Kamalakanta Mahapatra"),
        ("Microprocessor Lab", 2, True, "Dr. Samit Ari"),
        ("Communication Lab", 2, True, "Dr. Sukadev Meher"),
    ],
    "ECE5B": [
        ("Digital Communication", 3, False, "Dr. Sukadev Meher"),
        ("Microprocessors & Microcontrollers", 3, False, "Dr. Samit Ari"),
        ("Control Systems", 3, False, "Dr. Umesh Chandra Pati"),
        ("Electromagnetic Theory", 3, False, "Dr. Kamalakanta Mahapatra"),
        ("Microprocessor Lab", 2, True, "Dr. Samit Ari"),
        ("Communication Lab", 2, True, "Dr. Sukadev Meher"),
    ],

    # ----- ECE 7th Semester -----
    "ECE7A": [
        ("VLSI Design", 3, False, "Dr. Kamalakanta Mahapatra"),
        ("Wireless Communication", 3, False, "Dr. Sukadev Meher"),
        ("Digital Image Processing", 3, False, "Dr. Samit Ari"),
        ("Embedded Systems", 3, False, "Dr. Umesh Chandra Pati"),
        ("VLSI Lab", 2, True, "Dr. Kamalakanta Mahapatra"),
    ],
    "ECE7B": [
        ("VLSI Design", 3, False, "Dr. Kamalakanta Mahapatra"),
        ("Wireless Communication", 3, False, "Dr. Sukadev Meher"),
        ("Digital Image Processing", 3, False, "Dr. Samit Ari"),
        ("Embedded Systems", 3, False, "Dr. Umesh Chandra Pati"),
        ("VLSI Lab", 2, True, "Dr. Kamalakanta Mahapatra"),
    ],

    # ----- EE 3rd Semester -----
    "EE3A": [
        ("Electrical Machines-I", 3, False, "Dr. Anup Kumar Panda"),
        ("Analog Electronics", 3, False, "Dr. Kanungo Barada Mohanty"),
        ("Signals & Systems", 3, False, "Dr. Bidyadhar Subudhi"),
        ("Electrical Measurements", 3, False, "Dr. Susovan Samanta"),
        ("Machines Lab", 2, True, "Dr. Anup Kumar Panda"),
        ("Analog Electronics Lab", 2, True, "Dr. Kanungo Barada Mohanty"),
    ],

    # ----- EE 5th Semester -----
    "EE5A": [
        ("Power Systems-I", 3, False, "Dr. Anup Kumar Panda"),
        ("Control Systems", 3, False, "Dr. Bidyadhar Subudhi"),
        ("Power Electronics", 3, False, "Dr. Kanungo Barada Mohanty"),
        ("Electrical Machines-II", 3, False, "Dr. Susovan Samanta"),
        ("Power Electronics Lab", 2, True, "Dr. Kanungo Barada Mohanty"),
        ("Control Systems Lab", 2, True, "Dr. Bidyadhar Subudhi"),
    ],

    # ----- EE 7th Semester -----
    "EE7A": [
        ("Power Systems Protection", 3, False, "Dr. Anup Kumar Panda"),
        ("Industrial Drives", 3, False, "Dr. Kanungo Barada Mohanty"),
        ("Smart Grid Technology", 3, False, "Dr. Bidyadhar Subudhi"),
        ("High Voltage Engineering", 3, False, "Dr. Susovan Samanta"),
        ("Drives Lab", 2, True, "Dr. Kanungo Barada Mohanty"),
    ],

    # ----- ME 3rd Semester -----
    "ME3A": [
        ("Thermodynamics", 3, False, "Dr. Rabiranjan Murmu"),
        ("Strength of Materials", 3, False, "Dr. Subrata Kumar Panda"),
        ("Manufacturing Science-I", 3, False, "Dr. Saurav Datta"),
        ("Fluid Mechanics", 3, False, "Dr. Manoj Kumar Moharana"),
        ("Workshop Lab", 2, True, "Dr. Saurav Datta"),
        ("Engineering Mathematics-III", 3, False, "Dr. Manas Ranjan Tripathy"),
    ],
    "ME3B": [
        ("Thermodynamics", 3, False, "Dr. Rabiranjan Murmu"),
        ("Strength of Materials", 3, False, "Dr. Subrata Kumar Panda"),
        ("Manufacturing Science-I", 3, False, "Dr. Saurav Datta"),
        ("Fluid Mechanics", 3, False, "Dr. Manoj Kumar Moharana"),
        ("Workshop Lab", 2, True, "Dr. Saurav Datta"),
        ("Engineering Mathematics-III", 3, False, "Dr. Manas Ranjan Tripathy"),
    ],

    # ----- ME 5th Semester -----
    "ME5A": [
        ("Heat Transfer", 3, False, "Dr. Manoj Kumar Moharana"),
        ("Machine Design-I", 3, False, "Dr. Subrata Kumar Panda"),
        ("Manufacturing Science-II", 3, False, "Dr. Saurav Datta"),
        ("Industrial Engineering", 3, False, "Dr. Rabiranjan Murmu"),
        ("Heat Transfer Lab", 2, True, "Dr. Manoj Kumar Moharana"),
        ("CAD/CAM Lab", 2, True, "Dr. Subrata Kumar Panda"),
    ],
    "ME5B": [
        ("Heat Transfer", 3, False, "Dr. Manoj Kumar Moharana"),
        ("Machine Design-I", 3, False, "Dr. Subrata Kumar Panda"),
        ("Manufacturing Science-II", 3, False, "Dr. Saurav Datta"),
        ("Industrial Engineering", 3, False, "Dr. Rabiranjan Murmu"),
        ("Heat Transfer Lab", 2, True, "Dr. Manoj Kumar Moharana"),
        ("CAD/CAM Lab", 2, True, "Dr. Subrata Kumar Panda"),
    ],

    # ----- ME 7th Semester -----
    "ME7A": [
        ("Refrigeration & Air Conditioning", 3, False, "Dr. Rabiranjan Murmu"),
        ("Robotics", 3, False, "Dr. Subrata Kumar Panda"),
        ("Advanced Manufacturing", 3, False, "Dr. Saurav Datta"),
        ("Finite Element Methods", 3, False, "Dr. Manoj Kumar Moharana"),
        ("Robotics Lab", 2, True, "Dr. Subrata Kumar Panda"),
    ],
    "ME7B": [
        ("Refrigeration & Air Conditioning", 3, False, "Dr. Rabiranjan Murmu"),
        ("Robotics", 3, False, "Dr. Subrata Kumar Panda"),
        ("Advanced Manufacturing", 3, False, "Dr. Saurav Datta"),
        ("Finite Element Methods", 3, False, "Dr. Manoj Kumar Moharana"),
        ("Robotics Lab", 2, True, "Dr. Subrata Kumar Panda"),
    ],
}


def seed():
    """Populate the database with NIT Rourkela data and auto-generate timetables."""
    with app.app_context():
        # Create all tables if they don't exist (fresh DB)
        db.create_all()

        # Create admin user if missing
        if not User.query.first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

            faculty = User(username='faculty', role='faculty')
            faculty.set_password('faculty123')
            db.session.add(faculty)

            student = User(username='student', role='student')
            student.set_password('student123')
            db.session.add(student)

            db.session.commit()

        # Check if data already exists
        if Batch.query.first():
            print("Database already has data! To re-seed, delete instance/timetable.db first.")
            return

        print("=" * 60)
        print("  SEEDING NIT ROURKELA TIMETABLE DATA")
        print("=" * 60)

        # --- 1. Add Classrooms ---
        print(f"\n[1/4] Adding {len(CLASSROOMS)} Classrooms...")
        for name, capacity in CLASSROOMS:
            db.session.add(Classroom(name=name, capacity=capacity))
        db.session.commit()
        print("  Done!")

        # --- 2. Add Labs ---
        print(f"\n[2/4] Adding {len(LABS)} Labs...")
        for name, capacity in LABS:
            db.session.add(Lab(name=name, capacity=capacity))
        db.session.commit()
        print("  Done!")

        # --- 3. Add Batches ---
        print(f"\n[3/4] Adding {len(BATCHES)} Batches...")
        batch_objects = {}
        for batch_name in BATCHES:
            batch = Batch(name=batch_name)
            db.session.add(batch)
            db.session.flush()  # Get the ID immediately
            batch_objects[batch_name] = batch
        db.session.commit()
        print("  Done!")

        # --- 4. Schedule Courses for Each Batch ---
        print(f"\n[4/4] Scheduling courses for each batch...")
        total_scheduled = 0
        total_failed = 0

        for batch_name, courses in BATCH_COURSES.items():
            batch = batch_objects[batch_name]
            print(f"\n  Batch: {batch_name}")

            for course_name, credits, is_lab, professor_name in courses:
                # Get or create course
                course = Course.query.filter_by(name=course_name).first()
                if not course:
                    course = Course(
                        name=course_name,
                        credits=credits,
                        is_lab=is_lab,
                        priority=False
                    )
                    db.session.add(course)
                    db.session.flush()

                # Get or create professor
                professor = Professor.query.filter_by(name=professor_name).first()
                if not professor:
                    professor = Professor(name=professor_name)
                    db.session.add(professor)
                    db.session.flush()

                db.session.commit()

                # --- Schedule the course ---
                if is_lab:
                    # Find 2 consecutive free slots
                    placed = False
                    days = list(range(5))
                    random.shuffle(days)
                    for day in days:
                        for slot in range(8):
                            if slot == 4 or slot == 3:
                                continue  # Skip lunch break area
                            if (is_slot_available(batch.id, professor.id, day, slot) and
                                    is_slot_available(batch.id, professor.id, day, slot + 1)):
                                lab_room = find_available_lab(day, slot)
                                if lab_room:
                                    for offset in range(2):
                                        db.session.add(Schedule(
                                            batch_id=batch.id,
                                            course_id=course.id,
                                            professor_id=professor.id,
                                            day=day,
                                            slot=slot + offset,
                                            lab_id=lab_room.id
                                        ))
                                    db.session.commit()
                                    placed = True
                                    total_scheduled += 1
                                    print(f"    [LAB] {course_name} -> Day {day}, Slots {slot}-{slot+1}")
                                    break
                        if placed:
                            break
                    if not placed:
                        total_failed += 1
                        print(f"    [FAIL] Could not schedule lab: {course_name}")

                else:
                    # Regular course: place 'credits' number of 1-hour slots on different days
                    available = []
                    days = list(range(5))
                    random.shuffle(days)
                    for day in days:
                        slots = list(range(9))
                        random.shuffle(slots)
                        for slot in slots:
                            if slot == 4:
                                continue  # Skip lunch
                            if is_slot_available(batch.id, professor.id, day, slot):
                                classroom = find_available_classroom(day, slot)
                                if classroom:
                                    available.append((day, slot, classroom.id))
                                    break  # One slot per day

                    if len(available) >= credits:
                        chosen = available[:credits]
                        for day, slot, classroom_id in chosen:
                            db.session.add(Schedule(
                                batch_id=batch.id,
                                course_id=course.id,
                                professor_id=professor.id,
                                day=day,
                                slot=slot,
                                classroom_id=classroom_id
                            ))
                        db.session.commit()
                        total_scheduled += 1
                        days_str = ", ".join(f"Day {d} Slot {s}" for d, s, _ in chosen)
                        print(f"    [OK]  {course_name} ({credits}cr) -> {days_str}")
                    else:
                        total_failed += 1
                        print(f"    [FAIL] Not enough slots for: {course_name}")

        # --- Summary ---
        print("\n" + "=" * 60)
        print(f"  SEEDING COMPLETE!")
        print(f"  Classrooms: {len(CLASSROOMS)}")
        print(f"  Labs:       {len(LABS)}")
        print(f"  Batches:    {len(BATCHES)}")
        print(f"  Courses scheduled: {total_scheduled}")
        if total_failed:
            print(f"  Failed:     {total_failed} (conflicts / no rooms)")
        print("=" * 60)
        print("\nStart the app with: python app.py")
        print("Login: admin / admin123")


if __name__ == "__main__":
    seed()
