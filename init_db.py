# ============================================================================
# init_db.py — Database Initialization Script
# ============================================================================
#
# WHAT THIS DOES:
# This is a standalone script you can run to create (or reset) the database.
# It imports the app and db from app.py, then calls db.create_all() which
# reads all the Model classes and creates the corresponding SQL tables.
#
# WHEN TO USE:
# - First time setup (creates the database file)
# - If you add new models/columns and need to recreate tables
#
# HOW TO RUN:
#   python init_db.py
#
# NOTE: Running `python app.py` also creates the database automatically
# (see the `if __name__ == '__main__'` block in app.py), so this script
# is mainly useful if you want to initialize the DB without starting the server.
# ============================================================================

from app import app, db

with app.app_context():
    db.create_all()
    print("Database initialized successfully!")
