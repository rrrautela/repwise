import sqlite3
import json

DB_PATH = "repwise.db"


def init_db():
    # Connect to SQLite; creates the DB file if needed
    conn = sqlite3.connect(DB_PATH)

    # Store individual sets as JSON text
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workout_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise TEXT NOT NULL,
            sets_json TEXT NOT NULL,
            rpe INTEGER,
            notes TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    # Save changes and close the connection
    conn.commit()
    conn.close()


def insert_entry(workout):
    # Convert each SetEntry into a normal dictionary
    sets_data = [
        {
            "weight": set_entry.weight,
            "reps": set_entry.reps,
        }
        for set_entry in workout.sets
    ]

    # Convert the list of sets into JSON for SQLite
    sets_json = json.dumps(sets_data)

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO workout_entries
        (exercise, sets_json, rpe, notes, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            workout.exercise,
            sets_json,
            workout.rpe,
            workout.notes,
            workout.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.commit()
    conn.close()


def print_table():
    # Fetch every workout entry
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute("""
    SELECT * FROM workout_entries
    ORDER BY timestamp
    """)

    rows = cursor.fetchall()
    conn.close()

    # Print table header
    print("\n" + "=" * 100)
    print(
        f"{'ID':<5} {'Exercise':<20} {'Sets':<45} {'RPE':<5} {'Notes':<25} {'Timestamp'}"
    )
    print("=" * 100)

    # Print every row
    for row in rows:
        print(
            f"{row[0]:<5} "
            f"{row[1]:<20} "
            f"{row[2]:<45} "
            f"{str(row[3]):<5} "
            f"{str(row[4]):<25} "
            f"{row[5]}"
        )

    print("=" * 100)


def fetch_by_exercise(exercise, limit=8):
    # Fetch the most recent sessions for an exercise
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        SELECT *
        FROM workout_entries
        WHERE exercise = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (exercise, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


def fetch_exercises():
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        """
        SELECT DISTINCT exercise
        FROM workout_entries
        ORDER BY exercise
        """
    )

    exercises = [
        row[0]
        for row in cursor.fetchall()
    ]

    conn.close()

    return exercises

if __name__ == "__main__":
    # Initialize the database
    # init_db()
    # Print the current contents of the table
    print_table()
