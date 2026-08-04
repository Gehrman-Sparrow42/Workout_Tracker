import sqlite3
import json
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workout_tracker.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Exercises table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        instructions TEXT,
        default_sets INTEGER DEFAULT 3,
        default_reps INTEGER DEFAULT 10,
        default_duration INTEGER DEFAULT 0,
        is_bodyweight INTEGER DEFAULT 1
    );
    """)
    
    # 2. Workout logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, -- YYYY-MM-DD
        exercise_id INTEGER NOT NULL,
        sets_json TEXT NOT NULL, -- JSON list of dicts: [{"reps": 12, "weight": 0, "completed": 1}]
        notes TEXT,
        is_planned INTEGER DEFAULT 0, -- 1 = Planned, 0 = Done
        completed_at TEXT, -- Timestamp when completed
        FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
    );
    """)
    # 3. Calories logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calories_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE, -- YYYY-MM-DD
        calories INTEGER NOT NULL,
        protein REAL DEFAULT 0.0,
        carbs REAL DEFAULT 0.0,
        fat REAL DEFAULT 0.0,
        notes TEXT
    );
    """)

    # 4. Cardio logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cardio_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, -- YYYY-MM-DD
        exercise_name TEXT NOT NULL,
        duration_minutes REAL NOT NULL,
        distance_km REAL DEFAULT 0.0,
        calories_burned INTEGER DEFAULT 0,
        notes TEXT
    );
    """)

    # 5. Body logs (weight tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS body_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE, -- YYYY-MM-DD
        weight REAL NOT NULL,
        notes TEXT
    );
    """)
    # Seed exercises using INSERT OR IGNORE so new ones are always added to existing DBs
    default_exercises = [
        # --- Original defaults ---
        ("Push-ups",        "Chest",
         "Place hands shoulder-width apart, keep body in a straight line from head to heels, lower chest to floor. "
         "Tip: place books under your hands later to increase range of motion.",
         3, 15, 0, 1),
        ("Pull-ups",        "Back",
         "Hang from a bar with palms facing away, pull chest up to the bar, lower with control. "
         "Start bodyweight; add a weight belt once you can hit the top of your rep range consistently.",
         3, 8, 0, 1),
        ("Plank",           "Core",
         "Elbows under shoulders, keep body straight and core tight. Hold position.",
         3, 0, 60, 1),
        ("Squats",          "Legs",
         "Feet shoulder-width apart, lower hips back and down, keep chest up, return to standing.",
         3, 20, 0, 1),
        ("Dips",            "Arms",
         "Using parallel bars or a bench, lower hips by bending elbows to 90 degrees, push back up.",
         3, 10, 0, 1),
        ("Diamond Push-ups","Chest",
         "Place hands close together forming a diamond shape under your chest, lower chest to hands.",
         3, 10, 0, 1),
        ("Chin-ups",        "Back",
         "Hang from a bar with palms facing you (supinated grip), pull chin above bar with control.",
         3, 8, 0, 1),
        # --- New exercises ---
        ("Weighted Pull-up", "Back",
         "Hang from a bar with palms facing away. Attach extra weight via a dipping belt or hold a dumbbell between your feet. "
         "Pull chest to bar, lower with full control. Start bodyweight; add weight only when you can complete all reps cleanly.",
         3, 8, 0, 0),
        ("Bulgarian Split Squat", "Legs",
         "Stand ~2 feet in front of a bench. Place rear foot on the bench, laces down. "
         "Lower your front knee toward the floor keeping your torso upright, then drive through the front heel to stand. "
         "Hold a dumbbell in each hand (e.g. 10-15 kg each) or use bodyweight first. Complete all reps on one leg before switching.",
         3, 10, 0, 0),
        ("DB Lateral Raise", "Shoulders",
         "Stand holding a dumbbell in each hand (2x5 kg). With a slight elbow bend, raise arms out to the sides until "
         "they are parallel to the floor. Lower slowly and under control — the negative is where the gains happen. "
         "Avoid shrugging or swinging.",
         3, 13, 0, 0),
        ("Single-Arm Dumbbell Row", "Back",
         "Place one hand and same-side knee on a bench for support. Hold a heavy dumbbell in the other hand (aim for max weight, e.g. 15 kg). "
         "Pull the dumbbell up toward your hip, keeping elbow close to body. Lower with control. "
         "Complete all reps on one arm before switching.",
         3, 10, 0, 0),
        ("Single-Leg Romanian Deadlift", "Legs",
         "Stand on one leg holding a dumbbell in the opposite hand. Hinge forward at the hip, extending the free leg behind you, "
         "until your torso is roughly parallel to the floor. Keep a neutral spine. Drive through the standing heel to return. "
         "Use a wall or doorframe lightly for balance if needed. Switch legs after all reps.",
         3, 10, 0, 0),
        ("Pike Push-up", "Shoulders",
         "Start in a downward dog position (hips high, body forms an inverted V). Bend elbows to lower the crown of your head "
         "toward the floor between your hands, then press back up. The more vertical your body, the harder it hits your shoulders.",
         3, 10, 0, 1),
        ("DB Shoulder Press", "Shoulders",
         "Sit or stand holding a dumbbell in each hand at shoulder height, palms forward. "
         "Press both dumbbells overhead until arms are fully extended, then lower with control. "
         "Can also be performed single-arm with an adjustable dumbbell.",
         3, 10, 0, 0),
        ("Hanging Leg Raise", "Core",
         "Hang from a pull-up bar with an overhand grip, shoulders engaged (not passive). "
         "Raise your legs by flexing your hips and core — knees bent is easier, straight legs are harder. "
         "Lower slowly and avoid swinging. Do as many clean reps as possible each set.",
         3, 10, 0, 1),
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO exercises (name, category, instructions, default_sets, default_reps, default_duration, is_bodyweight)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, default_exercises)

    # 6. Stretches table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stretches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        instructions TEXT,
        default_sets INTEGER DEFAULT 3,
        default_duration INTEGER DEFAULT 30
    );
    """)

    # 7. Stretching logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stretching_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL, -- YYYY-MM-DD
        stretch_id INTEGER NOT NULL,
        sets_json TEXT NOT NULL, -- JSON list of dicts: [{"duration": 30, "completed": 1}]
        notes TEXT,
        is_planned INTEGER DEFAULT 0, -- 1 = Planned, 0 = Done
        completed_at TEXT, -- Timestamp when completed
        FOREIGN KEY (stretch_id) REFERENCES stretches (id) ON DELETE CASCADE
    );
    """)

    # Seed stretches
    default_stretches = [
        ("Hamstring Stretch", "Legs", "Sit on the floor, extend one leg forward, fold the other leg in. Reach towards your toes and hold.", 3, 30),
        ("Chest Doorway Stretch", "Chest", "Place your forearms on the doorway and gently lean forward until you feel a stretch in your chest.", 3, 30),
        ("Cobra Stretch", "Core", "Lie face down, place hands under shoulders, press up keeping hips on the floor to stretch the abs.", 3, 30),
        ("Child's Pose", "Back", "Kneel, sit back on your heels, reach your arms forward on the floor and lower your forehead down.", 3, 45),
        ("Calf Wall Stretch", "Legs", "Place hands on wall, step one leg back keeping it straight and press the heel into the floor.", 3, 30),
        ("Upper Trap Stretch", "Shoulders", "Gently pull your head down and to one side, reaching the opposite arm down to stretch the neck/shoulder.", 3, 30),
        ("Couch Stretch", "Legs", "Place one knee against a wall, step the other foot forward, and raise your torso upright to stretch the hip flexors.", 3, 45),
        ("Hanging Lat Stretch", "Back", "Hang from a pull-up bar, relaxed, letting your spine decompress and stretch your lats.", 3, 30)
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO stretches (name, category, instructions, default_sets, default_duration)
    VALUES (?, ?, ?, ?, ?)
    """, default_stretches)

    conn.commit()
    conn.close()

# --- Exercises CRUD ---
def add_exercise(name, category, instructions, default_sets=3, default_reps=10, default_duration=0, is_bodyweight=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO exercises (name, category, instructions, default_sets, default_reps, default_duration, is_bodyweight)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, category, instructions, default_sets, default_reps, default_duration, is_bodyweight))
        conn.commit()
        last_id = cursor.lastrowid
        return last_id, None
    except sqlite3.IntegrityError:
        return None, "An exercise with this name already exists."
    finally:
        conn.close()

def get_exercises():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exercises ORDER BY category, name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_exercise_by_id(exercise_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_exercise(exercise_id, name, category, instructions, default_sets, default_reps, default_duration, is_bodyweight):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE exercises
        SET name = ?, category = ?, instructions = ?, default_sets = ?, default_reps = ?, default_duration = ?, is_bodyweight = ?
        WHERE id = ?
        """, (name, category, instructions, default_sets, default_reps, default_duration, is_bodyweight, exercise_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "An exercise with this name already exists."
    finally:
        conn.close()

def delete_exercise(exercise_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()

# --- Workout Logs CRUD ---
def add_workout_log(date, exercise_id, sets_json, notes="", is_planned=0, completed_at=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO workout_logs (date, exercise_id, sets_json, notes, is_planned, completed_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (date, exercise_id, sets_json, notes, is_planned, completed_at))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_workout_logs(date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if date:
        cursor.execute("""
        SELECT wl.*, e.name as exercise_name, e.category as exercise_category, e.instructions as exercise_instructions
        FROM workout_logs wl
        JOIN exercises e ON wl.exercise_id = e.id
        WHERE wl.date = ?
        ORDER BY wl.is_planned DESC, wl.id ASC
        """, (date,))
    else:
        cursor.execute("""
        SELECT wl.*, e.name as exercise_name, e.category as exercise_category, e.instructions as exercise_instructions
        FROM workout_logs wl
        JOIN exercises e ON wl.exercise_id = e.id
        ORDER BY wl.date DESC, wl.is_planned DESC, wl.id ASC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_workout_dates():
    # Return a set of dates that have workouts (planned or done), cardio, calories, or weight logs
    conn = get_db_connection()
    cursor = conn.cursor()
    
    dates = {}
    
    # 1. Workout logs
    cursor.execute("SELECT DISTINCT date, is_planned FROM workout_logs")
    for r in cursor.fetchall():
        d = r['date']
        is_planned = r['is_planned']
        if d not in dates:
            dates[d] = {"has_planned": False, "has_done": False, "has_cardio": False, "has_calories": False, "has_body": False, "has_stretch": False}
        if is_planned == 1:
            dates[d]["has_planned"] = True
        else:
            dates[d]["has_done"] = True
            
    # 2. Cardio logs
    cursor.execute("SELECT DISTINCT date FROM cardio_logs")
    for r in cursor.fetchall():
        d = r['date']
        if d not in dates:
            dates[d] = {"has_planned": False, "has_done": False, "has_cardio": False, "has_calories": False, "has_body": False, "has_stretch": False}
        dates[d]["has_cardio"] = True
        
    # 3. Calories logs
    cursor.execute("SELECT DISTINCT date FROM calories_logs")
    for r in cursor.fetchall():
        d = r['date']
        if d not in dates:
            dates[d] = {"has_planned": False, "has_done": False, "has_cardio": False, "has_calories": False, "has_body": False, "has_stretch": False}
        dates[d]["has_calories"] = True
        
    # 4. Body logs
    cursor.execute("SELECT DISTINCT date FROM body_logs")
    for r in cursor.fetchall():
        d = r['date']
        if d not in dates:
            dates[d] = {"has_planned": False, "has_done": False, "has_cardio": False, "has_calories": False, "has_body": False, "has_stretch": False}
        dates[d]["has_body"] = True

    # 5. Stretching logs
    cursor.execute("SELECT DISTINCT date, is_planned FROM stretching_logs")
    for r in cursor.fetchall():
        d = r['date']
        is_planned = r['is_planned']
        if d not in dates:
            dates[d] = {"has_planned": False, "has_done": False, "has_cardio": False, "has_calories": False, "has_body": False, "has_stretch": False}
        if is_planned == 1:
            dates[d]["has_planned"] = True
        else:
            dates[d]["has_done"] = True
        dates[d]["has_stretch"] = True
        
    conn.close()
    return dates

def update_workout_log(log_id, sets_json, notes, is_planned, completed_at=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE workout_logs
    SET sets_json = ?, notes = ?, is_planned = ?, completed_at = ?
    WHERE id = ?
    """, (sets_json, notes, is_planned, completed_at, log_id))
    conn.commit()
    conn.close()

def delete_workout_log(log_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workout_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

# --- Export / Import Engine ---
def export_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all exercises
    cursor.execute("SELECT * FROM exercises")
    exercises = [dict(r) for r in cursor.fetchall()]
    
    # Get all workout logs
    cursor.execute("SELECT * FROM workout_logs")
    logs = [dict(r) for r in cursor.fetchall()]
    
    # Get all calories logs
    cursor.execute("SELECT * FROM calories_logs")
    calories = [dict(r) for r in cursor.fetchall()]

    # Get all cardio logs
    cursor.execute("SELECT * FROM cardio_logs")
    cardio = [dict(r) for r in cursor.fetchall()]

    # Get all body logs
    cursor.execute("SELECT * FROM body_logs")
    body = [dict(r) for r in cursor.fetchall()]

    # Get all stretches
    cursor.execute("SELECT * FROM stretches")
    stretches = [dict(r) for r in cursor.fetchall()]

    # Get all stretching logs
    cursor.execute("SELECT * FROM stretching_logs")
    stretching_logs = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "version": 1,
        "exported_at": datetime.now().isoformat(),
        "exercises": exercises,
        "workout_logs": logs,
        "calories_logs": calories,
        "cardio_logs": cardio,
        "body_logs": body,
        "stretches": stretches,
        "stretching_logs": stretching_logs
    }

def import_data(data_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing tables
        cursor.execute("DELETE FROM workout_logs")
        cursor.execute("DELETE FROM exercises")
        cursor.execute("DELETE FROM calories_logs")
        cursor.execute("DELETE FROM cardio_logs")
        cursor.execute("DELETE FROM body_logs")
        cursor.execute("DELETE FROM stretching_logs")
        cursor.execute("DELETE FROM stretches")
        
        # Insert exercises
        for ex in data_dict.get("exercises", []):
            cursor.execute("""
            INSERT INTO exercises (id, name, category, instructions, default_sets, default_reps, default_duration, is_bodyweight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ex['id'], ex['name'], ex['category'], ex['instructions'], ex['default_sets'], ex['default_reps'], ex['default_duration'], ex['is_bodyweight']))
            
        # Insert workout logs
        for log in data_dict.get("workout_logs", []):
            cursor.execute("""
            INSERT INTO workout_logs (id, date, exercise_id, sets_json, notes, is_planned, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (log['id'], log['date'], log['exercise_id'], log['sets_json'], log.get('notes', ""), log.get('is_planned', 0), log.get('completed_at')))
            
        # Insert calories logs
        for cal in data_dict.get("calories_logs", []):
            cursor.execute("""
            INSERT INTO calories_logs (id, date, calories, protein, carbs, fat, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cal['id'], cal['date'], cal['calories'], cal.get('protein', 0.0), cal.get('carbs', 0.0), cal.get('fat', 0.0), cal.get('notes', "")))

        # Insert cardio logs
        for card in data_dict.get("cardio_logs", []):
            cursor.execute("""
            INSERT INTO cardio_logs (id, date, exercise_name, duration_minutes, distance_km, calories_burned, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (card['id'], card['date'], card['exercise_name'], card['duration_minutes'], card.get('distance_km', 0.0), card.get('calories_burned', 0), card.get('notes', "")))

        # Insert body logs
        for bd in data_dict.get("body_logs", []):
            cursor.execute("""
            INSERT INTO body_logs (id, date, weight, notes)
            VALUES (?, ?, ?, ?)
            """, (bd['id'], bd['date'], bd['weight'], bd.get('notes', "")))

        # Insert stretches
        for st in data_dict.get("stretches", []):
            cursor.execute("""
            INSERT INTO stretches (id, name, category, instructions, default_sets, default_duration)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (st['id'], st['name'], st['category'], st['instructions'], st.get('default_sets', 3), st.get('default_duration', 30)))

        # Insert stretching logs
        for log in data_dict.get("stretching_logs", []):
            cursor.execute("""
            INSERT INTO stretching_logs (id, date, stretch_id, sets_json, notes, is_planned, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (log['id'], log['date'], log['stretch_id'], log['sets_json'], log.get('notes', ""), log.get('is_planned', 0), log.get('completed_at')))
            
        conn.commit()
        return True, "Data imported successfully!"
    except Exception as e:
        conn.rollback()
        return False, f"Import failed: {str(e)}"
    finally:
        conn.close()

# --- Calories CRUD ---
def get_calories_log(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM calories_logs WHERE date = ?", (date,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_calories_log(date, calories, protein=0.0, carbs=0.0, fat=0.0, notes=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR REPLACE INTO calories_logs (date, calories, protein, carbs, fat, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (date, calories, protein, carbs, fat, notes))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_calories_log(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM calories_logs WHERE date = ?", (date,))
    conn.commit()
    conn.close()

# --- Cardio CRUD ---
def get_cardio_logs(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cardio_logs WHERE date = ? ORDER BY id ASC", (date,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_cardio_log(date, exercise_name, duration_minutes, distance_km=0.0, calories_burned=0, notes=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO cardio_logs (date, exercise_name, duration_minutes, distance_km, calories_burned, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (date, exercise_name, duration_minutes, distance_km, calories_burned, notes))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def delete_cardio_log(log_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cardio_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

# --- Body State (Weight) CRUD ---
def get_body_log(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM body_logs WHERE date = ?", (date,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_body_log(date, weight, notes=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR REPLACE INTO body_logs (date, weight, notes)
        VALUES (?, ?, ?)
        """, (date, weight, notes))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_body_log(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM body_logs WHERE date = ?", (date,))
    conn.commit()
    conn.close()

# --- Stretches CRUD ---
def add_stretch(name, category, instructions, default_sets=3, default_duration=30):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO stretches (name, category, instructions, default_sets, default_duration)
        VALUES (?, ?, ?, ?, ?)
        """, (name, category, instructions, default_sets, default_duration))
        conn.commit()
        last_id = cursor.lastrowid
        return last_id, None
    except sqlite3.IntegrityError:
        return None, "A stretch with this name already exists."
    finally:
        conn.close()

def get_stretches():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stretches ORDER BY category, name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stretch_by_id(stretch_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stretches WHERE id = ?", (stretch_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_stretch(stretch_id, name, category, instructions, default_sets, default_duration):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE stretches
        SET name = ?, category = ?, instructions = ?, default_sets = ?, default_duration = ?
        WHERE id = ?
        """, (name, category, instructions, default_sets, default_duration, stretch_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "A stretch with this name already exists."
    finally:
        conn.close()

def delete_stretch(stretch_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stretches WHERE id = ?", (stretch_id,))
    conn.commit()
    conn.close()

# --- Stretching Logs CRUD ---
def add_stretching_log(date, stretch_id, sets_json, notes="", is_planned=0, completed_at=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO stretching_logs (date, stretch_id, sets_json, notes, is_planned, completed_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (date, stretch_id, sets_json, notes, is_planned, completed_at))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_stretching_logs(date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if date:
        cursor.execute("""
        SELECT sl.*, s.name as stretch_name, s.category as stretch_category, s.instructions as stretch_instructions
        FROM stretching_logs sl
        JOIN stretches s ON sl.stretch_id = s.id
        WHERE sl.date = ?
        ORDER BY sl.is_planned DESC, sl.id ASC
        """, (date,))
    else:
        cursor.execute("""
        SELECT sl.*, s.name as stretch_name, s.category as stretch_category, s.instructions as stretch_instructions
        FROM stretching_logs sl
        JOIN stretches s ON sl.stretch_id = s.id
        ORDER BY sl.date DESC, sl.is_planned DESC, sl.id ASC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_stretching_log(log_id, sets_json, notes, is_planned, completed_at=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE stretching_logs
    SET sets_json = ?, notes = ?, is_planned = ?, completed_at = ?
    WHERE id = ?
    """, (sets_json, notes, is_planned, completed_at, log_id))
    conn.commit()
    conn.close()

def delete_stretching_log(log_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stretching_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()
