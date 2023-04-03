import sqlite3
from sqlite3 import Error
from flask import g
from flask import current_app as app

def get_db_connection():
    with app.app_context():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect('users.db')
            db.row_factory = sqlite3.Row
        return db

def close_db_connection(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_database_schema():
    conn, cursor = get_db_connection()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        cv_balance INTEGER DEFAULT 0
    );
    """)
    conn.commit()
