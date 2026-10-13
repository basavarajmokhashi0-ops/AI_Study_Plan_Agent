import sqlite3
import pandas as pd
from pathlib import Path

# ---------------- DATABASE CONFIGURATION ----------------

DB_PATH = Path(__file__).parent / "study_plans.db"


# ---------------- DATABASE CONNECTION ----------------

def get_connection():
    return sqlite3.connect(DB_PATH)


# ---------------- INITIALIZE DATABASE ----------------

def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exam_date TEXT,
                study_hours INTEGER,
                learning_level TEXT,
                schedule_json TEXT NOT NULL
            )
        """)
        connection.commit()


# ---------------- SAVE STUDY PLAN ----------------

def save_study_plan(
    student_name,
    exam_date,
    study_hours,
    learning_level,
    schedule
):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO study_plans (
                student_name,
                exam_date,
                study_hours,
                learning_level,
                schedule_json
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            student_name,
            str(exam_date),
            study_hours,
            learning_level,
            schedule.to_json(orient="records")
        ))

        connection.commit()
        return cursor.lastrowid


# ---------------- GET SAVED PLANS ----------------

def get_saved_plans():
    with get_connection() as connection:
        return pd.read_sql_query("""
            SELECT
                id,
                student_name,
                created_at,
                exam_date,
                study_hours,
                learning_level
            FROM study_plans
            ORDER BY id DESC
        """, connection)


# ---------------- LOAD STUDY PLAN ----------------

def load_study_plan(plan_id):
    with get_connection() as connection:
        row = connection.execute("""
            SELECT schedule_json
            FROM study_plans
            WHERE id = ?
        """, (plan_id,)).fetchone()

    if row is None:
        return None

    return pd.read_json(row[0], orient="records")


# ---------------- UPDATE STUDY PLAN ----------------

def update_study_plan(plan_id, schedule):
    with get_connection() as connection:
        connection.execute("""
            UPDATE study_plans
            SET schedule_json = ?
            WHERE id = ?
        """, (
            schedule.to_json(orient="records"),
            plan_id
        ))

        connection.commit()


# Initialize the database when this module is imported
initialize_database()