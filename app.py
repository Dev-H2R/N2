"""
NeuroGym Analytics — Main Flask Application
Run with: python app.py
Then open: http://127.0.0.1:5000
"""
import os, sys, json, random, hashlib
from datetime import datetime
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash)

sys.path.insert(0, os.path.dirname(__file__))

from models.athlete import Athlete, WorkoutSession, Exercise, TrainingPlan
from utils.pipeline import (filter_by_level, filter_by_muscle, enrich_exercises,
                             sort_by_intensity, get_recommendations,
                             progressive_overload_generator)
from utils.vault import (load_exercises_json, save_session_csv, load_sessions_csv,
                         get_session_analytics, load_athletes_json,
                         save_athlete_json, VaultError)
from scraper.harvester import get_scraped_content

app = Flask(__name__)
app.secret_key = "neurogym-secret-2025"

DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        if not os.path.exists(USERS_FILE):
            return []
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def find_user(username):
    for u in load_users():
        if u["username"].lower() == username.lower():
            return u
    return None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "username" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm",  "").strip()
        name     = request.form.get("name",     "").strip()
        if not username or not password or not name:
            return render_template("signup.html", error="All fields are required.")
        if len(username) < 3:
            return render_template("signup.html", error="Username must be at least 3 characters.")
        if len(password) < 6:
            return render_template("signup.html", error="Password must be at least 6 characters.")
        if password != confirm:
            return render_template("signup.html", error="Passwords do not match.")
        if find_user(username):
            return render_template("signup.html", error="Username already taken.")
        users = load_users()
        users.append({"username": username, "password": hash_password(password),
                      "name": name, "joined": datetime.now().strftime("%Y-%m-%d"),
                      "level": "beginner", "goal": "general_fitness"})
        save_users(users)
        session["username"] = username
        session["name"]     = name
        flash(f"Welcome to NeuroGym, {name}!", "success")
        return redirect(url_for("home"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            return render_template("login.html", error="Please enter username and password.")
        user = find_user(username)
        if not user or user["password"] != hash_password(password):
            return render_template("login.html", error="Incorrect username or password.")
        session["username"] = user["username"]
        session["name"]     = user["name"]
        flash(f"Welcome back, {user['name']}!", "success")
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/")
def home():
    exercises = load_exercises_json()
    stats = {
        "exercise_count":  len(exercises),
        "muscle_groups":   len(set(e["muscle_group"] for e in exercises)),
        "equipment_types": len(set(e["equipment"]    for e in exercises)),
    }
    beginner_picks = get_recommendations(exercises, "beginner", 3)
    advanced_picks = get_recommendations(exercises, "advanced", 3)
    return render_template("home.html", stats=stats,
                           beginner_picks=beginner_picks,
                           advanced_picks=advanced_picks)

@app.route("/workouts")
def workouts():
    exercises = load_exercises_json()
    level  = request.args.get("level",  "all")
    muscle = request.args.get("muscle", "all")
    filtered = list(exercises)
    try:
        if level  != "all": filtered = filter_by_level(filtered,  level)  if filtered else []
        if muscle != "all": filtered = filter_by_muscle(filtered, muscle) if filtered else []
        if filtered:
            filtered = enrich_exercises(filtered)
            filtered = sort_by_intensity(filtered)
    except Exception:
        filtered = exercises
    muscle_groups = sorted(set(e["muscle_group"] for e in exercises))
    return render_template("workouts.html", exercises=filtered,
                           muscle_groups=muscle_groups,
                           levels=["beginner", "intermediate", "advanced"],
                           active_level=level, active_muscle=muscle,
                           total=len(filtered))

@app.route("/equipment")
def equipment():
    eq_type = request.args.get("type", "all")
    eq_list = get_equipment_data()
    if eq_type != "all":
        eq_list = [e for e in eq_list if e["type"] == eq_type]
    return render_template("equipment.html", equipment=eq_list, active_type=eq_type)

@app.route("/training")
def training():
    plans            = build_training_plans()
    overload_targets = list(progressive_overload_generator(60, 12, 2.5))
    return render_template("training.html", plans=plans, overload_targets=overload_targets)

@app.route("/dashboard")
@login_required
def dashboard():
    try:    analytics = get_session_analytics()
    except: analytics = {"total_sessions": 0, "total_calories": 0,
                         "total_volume_kg": 0, "avg_sets_per_session": 0,
                         "recent_sessions": [], "weekly_calories": []}
    athlete_data = {}
    try:
        athletes = load_athletes_json()
        if athletes:
            athlete_data = athletes[0]
            athlete_data["name"] = session.get("name", athlete_data.get("name", "Athlete"))
    except: pass
    sessions_data = load_sessions_csv()
    return render_template("dashboard.html", analytics=analytics,
                           athlete=athlete_data,
                           sessions=sessions_data[-10:] if sessions_data else [])

@app.route("/log", methods=["GET", "POST"])
@login_required
def log_session():
    exercises = load_exercises_json()
    if request.method == "POST":
        try:
            athlete_name = session.get("name", "Athlete")
            session_name = request.form.get("session_name", "").strip()
            day          = request.form.get("day", "Monday")
            duration     = int(request.form.get("duration_minutes", 60))
            ex_names     = request.form.getlist("exercises")
            if not session_name:
                return render_template("log.html", exercises=exercises, error="Please enter a session name.")
            if not ex_names:
                return render_template("log.html", exercises=exercises, error="Please select at least one exercise.")
            sess = WorkoutSession(session_name, day, athlete_name)
            sess.duration_minutes = duration
            sess.completed        = True
            for ex_dict in exercises:
                if ex_dict["name"] in ex_names:
                    ex_obj = Exercise(
                        name=ex_dict["name"], muscle_group=ex_dict["muscle_group"],
                        equipment=ex_dict["equipment"], level=ex_dict["level"],
                        sets=ex_dict["sets"], reps=str(ex_dict["reps"]),
                        rest_seconds=ex_dict["rest_seconds"],
                        calories_per_set=ex_dict["calories_per_set"],
                        description=ex_dict.get("description", ""),
                    )
                    sess.add_exercise(ex_obj)
            save_session_csv(sess.to_dict())
            try:
                athletes = load_athletes_json()
                if athletes:
                    a = athletes[0]
                    a["total_sessions"]        = int(a.get("total_sessions", 0)) + 1
                    a["total_calories_burned"] = round(float(a.get("total_calories_burned", 0)) + sess.total_calories(), 2)
                    a["total_volume_kg"]       = round(float(a.get("total_volume_kg", 0)) + sess.total_volume_kg(), 2)
                    save_athlete_json(a)
            except: pass
            flash("Session saved! Great work!", "success")
            return redirect(url_for("dashboard"))
        except VaultError as e:
            return render_template("log.html", exercises=exercises, error=str(e))
        except Exception as e:
            return render_template("log.html", exercises=exercises, error=f"Error: {e}")
    return render_template("log.html", exercises=exercises)

@app.route("/insights")
def insights():
    refresh = request.args.get("refresh") == "1"
    scraped = {"status": "error", "quotes": [], "books": [], "count": 0, "errors": []}
    try:
        scraped = get_scraped_content(force_refresh=refresh)
    except Exception as e:
        scraped["errors"] = [str(e)]
    daily_quote = None
    all_quotes  = scraped.get("quotes", [])
    if all_quotes:
        random.seed(int(datetime.now().strftime("%Y%m%d")))
        daily_quote = random.choice(all_quotes)
    fitness_tips = get_fitness_tips()
    return render_template("insights.html", data=scraped,
                           daily_quote=daily_quote, fitness_tips=fitness_tips)

@app.route("/api/exercises")
def api_exercises():
    exercises = load_exercises_json()
    level  = request.args.get("level")
    muscle = request.args.get("muscle")
    try:
        if level:  exercises = filter_by_level(exercises, level)
        if muscle: exercises = filter_by_muscle(exercises, muscle)
        exercises = enrich_exercises(exercises) if exercises else []
    except: pass
    return jsonify(exercises)

@app.route("/api/analytics")
def api_analytics():
    try:    return jsonify(get_session_analytics())
    except VaultError as e: return jsonify({"error": str(e)}), 500

def get_fitness_tips():
    return [
        {"icon": "💧", "title": "Hydrate",             "tip": "Drink 2–3 litres of water daily. Dehydration cuts performance by up to 20%."},
        {"icon": "😴", "title": "Sleep to Grow",        "tip": "Muscles grow during sleep, not in the gym. Aim for 7–9 hours every night."},
        {"icon": "🥩", "title": "Protein Matters",      "tip": "Eat 1.6–2.2g of protein per kg of bodyweight to maximise muscle growth."},
        {"icon": "📈", "title": "Progressive Overload", "tip": "Add a little more weight or reps each week. Consistency beats intensity."},
        {"icon": "🧘", "title": "Respect Recovery",     "tip": "Rest days are not lazy days. Your body repairs and grows stronger on off-days."},
        {"icon": "🍽️", "title": "Nutrition First",      "tip": "You cannot out-train a bad diet. 80% of your results come from what you eat."},
    ]

def get_equipment_data():
    return [
        {"name": "Olympic Barbell",      "type": "free",    "emoji": "📏", "muscles": ["Chest","Back","Legs","Shoulders"], "desc": "20 kg standard bar. The backbone of all compound lifts — bench, squat, deadlift, OHP.",      "tips": "Always use collars on plates. Use chalk for heavy pulls."},
        {"name": "Dumbbell Set",         "type": "free",    "emoji": "🏋️", "muscles": ["All Groups"],                      "desc": "Adjustable dumbbells 2–50 kg. Unilateral training for symmetry and stabiliser development.", "tips": "Start lighter than you think. Form always beats weight."},
        {"name": "EZ Curl Bar",          "type": "free",    "emoji": "〰️", "muscles": ["Biceps","Triceps"],                 "desc": "Angled bar that reduces wrist strain during curls and skull crushers.",                     "tips": "Angled grip reduces forearm pronation — easier on the wrists."},
        {"name": "Trap / Hex Bar",       "type": "free",    "emoji": "🔷", "muscles": ["Glutes","Hamstrings","Traps"],      "desc": "Hexagonal bar for deadlifts. More knee-friendly than conventional deadlift.",                 "tips": "Stand inside the frame. Drive hard through your heels."},
        {"name": "Kettlebells",          "type": "free",    "emoji": "🫙", "muscles": ["Full Body"],                        "desc": "Cast iron bells for swings, cleans, presses. Develops power and grip.",                      "tips": "Hinge, don't squat, on the swing. All power from the hips."},
        {"name": "Resistance Bands",     "type": "free",    "emoji": "🎀", "muscles": ["Full Body"],                        "desc": "Accommodating resistance for any exercise. Great for warm-up and rehab.",                    "tips": "Anchor low for pulling, high for pressing work."},
        {"name": "Cable Machine",        "type": "machine", "emoji": "🔗", "muscles": ["All Groups"],                       "desc": "Adjustable pulley system with constant tension — essential for isolation.",                   "tips": "Adjust pulley height for the target angle. Use slow eccentrics."},
        {"name": "Leg Press",            "type": "machine", "emoji": "🔩", "muscles": ["Quads","Glutes","Hamstrings"],      "desc": "45° sled machine for heavy lower body work without lower back stress.",                      "tips": "Feet high and wide = glutes. Feet low and narrow = quads."},
        {"name": "Lat Pulldown",         "type": "machine", "emoji": "⬇️", "muscles": ["Lats","Biceps"],                    "desc": "Overhead cable for back width. Swappable handles for different grip variations.",             "tips": "Lean back slightly, pull to upper chest, squeeze shoulder blades."},
        {"name": "Chest Fly / Pec Deck", "type": "machine", "emoji": "🦋", "muscles": ["Chest"],                            "desc": "Isolation for pectoral muscles with a controlled arc motion.",                               "tips": "Don't go past a comfortable stretch. Slow eccentric phase."},
        {"name": "Smith Machine",        "type": "machine", "emoji": "🏗️", "muscles": ["Chest","Shoulders","Legs"],        "desc": "Fixed vertical bar for safe heavy training solo.",                                           "tips": "Angle your body to compensate for the fixed bar path."},
        {"name": "Leg Curl Machine",     "type": "machine", "emoji": "🦿", "muscles": ["Hamstrings"],                       "desc": "Prone or seated hamstring isolation. Critical for balanced leg development.",                  "tips": "Full extension before curling. Don't swing the hips."},
        {"name": "Treadmill",            "type": "cardio",  "emoji": "🏃", "muscles": ["Cardio","Calves","Quads"],          "desc": "Motorised running belt 0–25 km/h with adjustable incline.",                                  "tips": "1% incline mimics outdoor running. Don't hold the rails."},
        {"name": "Rowing Machine",       "type": "cardio",  "emoji": "🚣", "muscles": ["Full Body"],                        "desc": "Full-body low-impact cardio. Engages 86% of muscle groups every stroke.",                    "tips": "Legs then hips then arms on drive. Reverse on recovery."},
        {"name": "Assault Bike",         "type": "cardio",  "emoji": "🚴", "muscles": ["Cardio","Arms","Legs"],             "desc": "Air resistance fan bike — scales with your effort. No max resistance.",                       "tips": "20s all-out, 40s recovery is a brutal and effective protocol."},
        {"name": "Stair Climber",        "type": "cardio",  "emoji": "🪜", "muscles": ["Glutes","Quads","Calves"],          "desc": "Low-impact, high-calorie machine. Great for glute activation.",                              "tips": "Don't lean on rails. Upright posture for full activation."},
        {"name": "Battle Ropes",         "type": "cardio",  "emoji": "〰️", "muscles": ["Shoulders","Core","Cardio"],        "desc": "Heavy rope training for conditioning and upper body endurance.",                             "tips": "Anchor at waist height. Alternate or simultaneous waves both work."},
    ]

def build_training_plans():
    p1 = TrainingPlan("Foundation Builder","beginner",8,3,"general_fitness",
                      "Perfect for newcomers. Build strength habits, master form, develop consistency.")
    p1.add_day("Monday","Full Body A",["Back Squat","Barbell Bench Press","Bent Over Row","Plank"])
    p1.add_day("Tuesday","Rest / Walk",[],rest=True)
    p1.add_day("Wednesday","Full Body B",["Romanian Deadlift","Overhead Press","Lat Pulldown","Hanging Leg Raise"])
    p1.add_day("Thursday","Rest / Stretch",[],rest=True)
    p1.add_day("Friday","Full Body C",["Leg Press","Incline Dumbbell Press","Seated Cable Row","Ab Wheel Rollout"])
    p1.add_day("Saturday","Rest",[],rest=True)
    p1.add_day("Sunday","Rest",[],rest=True)

    p2 = TrainingPlan("Power Hypertrophy","intermediate",12,4,"muscle_gain",
                      "Upper/lower split for simultaneous strength and muscle growth. The sweet spot.")
    p2.add_day("Monday","Upper Power",["Barbell Bench Press","Bent Over Row","Overhead Press","Barbell Curl"])
    p2.add_day("Tuesday","Lower Power",["Back Squat","Romanian Deadlift","Leg Press","Calf Raise"])
    p2.add_day("Wednesday","Active Recovery",[],rest=True)
    p2.add_day("Thursday","Upper Volume",["Incline Dumbbell Press","Lat Pulldown","Lateral Raise","Skull Crusher"])
    p2.add_day("Friday","Lower Volume",["Walking Lunge","Calf Raise","Hanging Leg Raise","Plank"])
    p2.add_day("Saturday","Rest",[],rest=True)
    p2.add_day("Sunday","Rest",[],rest=True)

    p3 = TrainingPlan("Elite PPL","advanced",16,6,"strength",
                      "Push/Pull/Legs high-frequency for experienced lifters chasing peak performance.")
    p3.add_day("Monday","Push A",["Barbell Bench Press","Overhead Press","Incline Dumbbell Press","Lateral Raise","Skull Crusher"])
    p3.add_day("Tuesday","Pull A",["Pull Up","Bent Over Row","Seated Cable Row","Face Pull","Barbell Curl"])
    p3.add_day("Wednesday","Legs A",["Back Squat","Romanian Deadlift","Leg Press","Calf Raise","Plank"])
    p3.add_day("Thursday","Push B",["Overhead Press","Cable Fly","Dips","Face Pull","Hammer Curl"])
    p3.add_day("Friday","Pull B",["Bent Over Row","Lat Pulldown","Seated Cable Row","Barbell Curl","Hanging Leg Raise"])
    p3.add_day("Saturday","Legs B",["Romanian Deadlift","Walking Lunge","Leg Press","Ab Wheel Rollout","HIIT Sprint Intervals"])
    p3.add_day("Sunday","Rest / Mobility",[],rest=True)

    return [p1.to_dict(), p2.to_dict(), p3.to_dict()]

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
