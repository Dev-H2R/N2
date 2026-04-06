"""
Run this ONCE before starting the app.
It creates all the data files needed.
"""
import json
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

EXERCISES = [
    {"name":"Barbell Bench Press","muscle_group":"chest","equipment":"barbell","level":"intermediate","sets":4,"reps":"5","rest_seconds":180,"calories_per_set":28,"total_calories":112,"description":"The king of chest exercises. Full pressing motion targeting pectorals, front delts, and triceps.","tips":"Plant feet firmly, slight arch in back, grip just outside shoulder-width.","emoji":"🏋️"},
    {"name":"Incline Dumbbell Press","muscle_group":"chest","equipment":"dumbbell","level":"beginner","sets":3,"reps":"10","rest_seconds":90,"calories_per_set":22,"total_calories":66,"description":"Targets upper chest with neutral grip. Greater range of motion than barbell.","tips":"Set bench to 30–45°. Don't flare elbows past 75°.","emoji":"📐"},
    {"name":"Cable Fly","muscle_group":"chest","equipment":"cable","level":"beginner","sets":3,"reps":"15","rest_seconds":60,"calories_per_set":16,"total_calories":48,"description":"Isolation for pectorals with constant cable tension throughout the movement.","tips":"Slight elbow bend, squeeze hard at the centre of chest.","emoji":"🔗"},
    {"name":"Dips","muscle_group":"chest","equipment":"bodyweight","level":"intermediate","sets":4,"reps":"12","rest_seconds":90,"calories_per_set":24,"total_calories":96,"description":"Bodyweight compound targeting triceps and chest. Lean forward for chest emphasis.","tips":"Lean torso forward 30° for chest activation. Keep shoulders down.","emoji":"💪"},
    {"name":"Pull Up","muscle_group":"back","equipment":"bodyweight","level":"advanced","sets":4,"reps":"8","rest_seconds":120,"calories_per_set":30,"total_calories":120,"description":"The ultimate upper back builder. Lats, rhomboids, biceps — full pulling movement.","tips":"Full dead hang start. Pull elbows to hips, not just chin to bar.","emoji":"⬆️"},
    {"name":"Bent Over Row","muscle_group":"back","equipment":"barbell","level":"intermediate","sets":4,"reps":"6","rest_seconds":180,"calories_per_set":32,"total_calories":128,"description":"Compound pull for full back thickness — lats, traps, rear delts, biceps.","tips":"Hinge at 45°, brace core, row to navel not chest.","emoji":"🏊"},
    {"name":"Lat Pulldown","muscle_group":"back","equipment":"cable","level":"beginner","sets":3,"reps":"12","rest_seconds":90,"calories_per_set":20,"total_calories":60,"description":"Machine-assisted lat isolation. Great for building the V-taper shape.","tips":"Lean back slightly, pull to upper chest, squeeze shoulder blades down.","emoji":"⬇️"},
    {"name":"Seated Cable Row","muscle_group":"back","equipment":"cable","level":"beginner","sets":3,"reps":"12","rest_seconds":90,"calories_per_set":18,"total_calories":54,"description":"Horizontal pull for mid-back thickness. Keep chest tall throughout.","tips":"Don't round lower back. Pause and squeeze at full contraction.","emoji":"🔄"},
    {"name":"Back Squat","muscle_group":"legs","equipment":"barbell","level":"advanced","sets":5,"reps":"5","rest_seconds":240,"calories_per_set":42,"total_calories":210,"description":"Foundation of lower body strength. Quads, glutes, hamstrings and core all work together.","tips":"Bar on upper traps, squat to parallel, drive knees out over toes.","emoji":"🦵"},
    {"name":"Romanian Deadlift","muscle_group":"legs","equipment":"barbell","level":"intermediate","sets":3,"reps":"10","rest_seconds":120,"calories_per_set":34,"total_calories":102,"description":"Hip hinge emphasising hamstrings and glutes with a deep stretch at the bottom.","tips":"Slight knee bend, push hips back, keep bar close to body throughout.","emoji":"🏋️"},
    {"name":"Leg Press","muscle_group":"legs","equipment":"machine","level":"beginner","sets":4,"reps":"12","rest_seconds":90,"calories_per_set":28,"total_calories":112,"description":"Machine lower body compound. Heavy loading possible without lower back stress.","tips":"Don't lock out knees at top. Full range of motion gives best results.","emoji":"🔩"},
    {"name":"Walking Lunge","muscle_group":"legs","equipment":"dumbbell","level":"beginner","sets":3,"reps":"12/leg","rest_seconds":90,"calories_per_set":22,"total_calories":66,"description":"Unilateral leg exercise for balance, stability and quad development.","tips":"90° knee angle front and back, keep torso upright, step through heel.","emoji":"🚶"},
    {"name":"Calf Raise","muscle_group":"legs","equipment":"machine","level":"beginner","sets":4,"reps":"20","rest_seconds":60,"calories_per_set":12,"total_calories":48,"description":"Isolation for gastrocnemius and soleus. High rep protocol works best.","tips":"Full stretch at bottom, pause at top. Use a slow controlled tempo.","emoji":"🦶"},
    {"name":"Overhead Press","muscle_group":"shoulders","equipment":"barbell","level":"intermediate","sets":4,"reps":"6","rest_seconds":180,"calories_per_set":30,"total_calories":120,"description":"Strict press for boulder shoulders and serious upper body pressing strength.","tips":"Bar starts on clavicle, press in slight arc, brace core hard throughout.","emoji":"☝️"},
    {"name":"Lateral Raise","muscle_group":"shoulders","equipment":"dumbbell","level":"beginner","sets":4,"reps":"15","rest_seconds":60,"calories_per_set":14,"total_calories":56,"description":"Medial deltoid isolation. Creates the wide shoulder look instantly.","tips":"Slight elbow bend, lead with elbows not hands, stop at shoulder height.","emoji":"🦅"},
    {"name":"Face Pull","muscle_group":"shoulders","equipment":"cable","level":"beginner","sets":3,"reps":"15","rest_seconds":60,"calories_per_set":14,"total_calories":42,"description":"Rear delt and rotator cuff health. Essential injury prevention exercise.","tips":"Cable at head height, pull to face, flare elbows out wide.","emoji":"🎯"},
    {"name":"Barbell Curl","muscle_group":"arms","equipment":"barbell","level":"beginner","sets":3,"reps":"10","rest_seconds":75,"calories_per_set":16,"total_calories":48,"description":"Classic bicep mass builder. Full supination for peak contraction.","tips":"No swinging. Pin elbows at sides and use full range of motion.","emoji":"💪"},
    {"name":"Skull Crusher","muscle_group":"arms","equipment":"barbell","level":"intermediate","sets":3,"reps":"10","rest_seconds":90,"calories_per_set":18,"total_calories":54,"description":"Lying tricep extension targeting the long head. Be careful and controlled.","tips":"Lower to forehead level, don't flare elbows, slow controlled descent.","emoji":"💀"},
    {"name":"Hammer Curl","muscle_group":"arms","equipment":"dumbbell","level":"beginner","sets":3,"reps":"12","rest_seconds":60,"calories_per_set":14,"total_calories":42,"description":"Neutral grip curl for brachialis and forearm thickness development.","tips":"Neutral grip throughout the full movement. Alternate arms for control.","emoji":"🔨"},
    {"name":"Plank","muscle_group":"core","equipment":"bodyweight","level":"beginner","sets":3,"reps":"60s","rest_seconds":60,"calories_per_set":10,"total_calories":30,"description":"Isometric anti-extension for deep core stability and posture.","tips":"Neutral spine, squeeze glutes, breathe steadily throughout.","emoji":"🧱"},
    {"name":"Hanging Leg Raise","muscle_group":"core","equipment":"bodyweight","level":"advanced","sets":4,"reps":"12","rest_seconds":60,"calories_per_set":18,"total_calories":72,"description":"Advanced abs through full hip flexion. No swinging or momentum.","tips":"Posterior pelvic tilt at top of movement. Control the descent slowly.","emoji":"🔄"},
    {"name":"Ab Wheel Rollout","muscle_group":"core","equipment":"ab wheel","level":"intermediate","sets":3,"reps":"10","rest_seconds":90,"calories_per_set":16,"total_calories":48,"description":"Advanced anti-extension movement. One of the most effective core exercises.","tips":"Brace hard before rolling. Don't let hips drop at any point.","emoji":"⚙️"},
    {"name":"HIIT Sprint Intervals","muscle_group":"cardio","equipment":"treadmill","level":"intermediate","sets":8,"reps":"30s on/90s off","rest_seconds":90,"calories_per_set":50,"total_calories":400,"description":"High-intensity intervals for maximum fat burn and cardiovascular fitness.","tips":"80–90% max heart rate on sprints. Walk during rest. Warm up 5 min first.","emoji":"🏃"},
    {"name":"Rowing Machine","muscle_group":"cardio","equipment":"rower","level":"beginner","sets":1,"reps":"20 min","rest_seconds":0,"calories_per_set":220,"total_calories":220,"description":"Full-body low-impact cardio. Engages 86% of all muscle groups simultaneously.","tips":"Legs then hips then arms on the pull. Reverse on the return stroke.","emoji":"🚣"},
    {"name":"Jump Rope","muscle_group":"cardio","equipment":"rope","level":"beginner","sets":5,"reps":"2 min","rest_seconds":60,"calories_per_set":40,"total_calories":200,"description":"Coordination, calf strength, and fat loss all in one simple tool.","tips":"Light grip, small jumps, land softly on balls of feet each time.","emoji":"🪢"},
]

SESSIONS = [
    {"session_name":"Upper Power","athlete_name":"Alex","date":"2025-03-20","day":"Monday","total_calories":340,"total_sets":18,"total_volume_kg":2850,"duration_minutes":65,"completed":True},
    {"session_name":"Lower Power","athlete_name":"Alex","date":"2025-03-21","day":"Tuesday","total_calories":420,"total_sets":20,"total_volume_kg":4200,"duration_minutes":75,"completed":True},
    {"session_name":"Upper Volume","athlete_name":"Alex","date":"2025-03-23","day":"Thursday","total_calories":310,"total_sets":24,"total_volume_kg":2200,"duration_minutes":80,"completed":True},
    {"session_name":"Lower Volume","athlete_name":"Alex","date":"2025-03-24","day":"Friday","total_calories":380,"total_sets":22,"total_volume_kg":3600,"duration_minutes":70,"completed":True},
    {"session_name":"Upper Power","athlete_name":"Alex","date":"2025-03-27","day":"Monday","total_calories":360,"total_sets":18,"total_volume_kg":3100,"duration_minutes":68,"completed":True},
    {"session_name":"Lower Power","athlete_name":"Alex","date":"2025-03-28","day":"Tuesday","total_calories":440,"total_sets":20,"total_volume_kg":4400,"duration_minutes":78,"completed":True},
    {"session_name":"Upper Volume","athlete_name":"Alex","date":"2025-03-30","day":"Thursday","total_calories":320,"total_sets":24,"total_volume_kg":2350,"duration_minutes":82,"completed":True},
    {"session_name":"Lower Volume","athlete_name":"Alex","date":"2025-03-31","day":"Friday","total_calories":390,"total_sets":22,"total_volume_kg":3750,"duration_minutes":72,"completed":True},
    {"session_name":"Upper Power","athlete_name":"Alex","date":"2025-04-01","day":"Tuesday","total_calories":370,"total_sets":18,"total_volume_kg":3300,"duration_minutes":66,"completed":True},
]

ATHLETES = [
    {"name":"Alex","age":24,"weight_kg":78,"height_cm":178,"goal":"muscle_gain","level":"intermediate",
     "bmi":24.6,"bmi_category":"Normal","bmr":1820,"total_sessions":9,
     "total_calories_burned":3330,"total_volume_kg":29750,"streak":14,"joined_date":"2025-01-15"}
]

# Write files
with open(os.path.join(DATA_DIR, "exercises.json"), "w") as f:
    json.dump(EXERCISES, f, indent=2)

csv_fields = ["session_name","athlete_name","date","day","total_calories","total_sets","total_volume_kg","duration_minutes","completed"]
with open(os.path.join(DATA_DIR, "sessions.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()
    writer.writerows(SESSIONS)

with open(os.path.join(DATA_DIR, "athletes.json"), "w") as f:
    json.dump(ATHLETES, f, indent=2)

print(f"✓ Seeded {len(EXERCISES)} exercises")
print(f"✓ Seeded {len(SESSIONS)} sessions")
print(f"✓ Seeded {len(ATHLETES)} athlete")
print("✓ Ready! Now run: python app.py")
