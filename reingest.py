from memory.manager import (
    create_user, create_goal, create_measurement, create_injury,
    create_fact, create_workout, create_exercise,add_message

)

# ============ USER 1: YOUSSEF (Hyrox/strength athlete) ============
y = create_user("Youssef", age=22, sex="M", height=180)

create_goal(y, "Sub-70 minute Hyrox", description="Finish Hyrox under 70 min", priority=1, target_date="2026-06-01")
create_goal(y, "Bench press 100kg", description="Hit a 100kg bench", priority=2)

create_measurement(y, weight=78, body_fat=14, resting_heart_rate=52, notes="Post off-season")

create_injury(y, body_part="left knee", description="Mild patellar tendinitis", severity="mild")

create_fact(y, "sport", "Hyrox and water polo")
create_fact(y, "training_time", "prefers morning workouts")
create_fact(y, "experience", "advanced, 5 years training")

# a workout with exercises
w1 = create_workout(y, workout_type="Push", duration=60, calories=400, notes="Felt strong")
create_exercise(w1, "Bench Press", sets=4, reps=8, weight=85, rir=2)
create_exercise(w1, "Overhead Press", sets=3, reps=10, weight=50, rir=2)

# ============ USER 2: MICHAEL (beginner, weight loss) ============
m = create_user("Michael", age=28, sex="M", height=175)

create_goal(m, "Lose 8kg", description="Drop from 90 to 82kg", priority=1, target_date="2026-05-01")
create_goal(m, "Run 5k without stopping", description="Build base cardio", priority=2)

create_measurement(m, weight=90, body_fat=24, resting_heart_rate=68, notes="Starting out")

create_injury(m, body_part="lower back", description="Occasional stiffness from desk work", severity="mild")

create_fact(m, "sport", "new to fitness")
create_fact(m, "training_time", "prefers evening workouts")
create_fact(m, "experience", "beginner, 2 months in")

w2 = create_workout(m, workout_type="Full body", duration=45, calories=300, notes="First proper session")
create_exercise(w2, "Goblet Squat", sets=3, reps=12, weight=20, rir=3)

print("Seeded Youssef (id", y, ") and Michael (id", m, ")")


# ============ USER 3: MOHAMED (intermediate, Hyrox/fitness) ============
mo = create_user("Mohamed", age=25, sex="M", height=178)

create_goal(mo, "Improve Hyrox performance", description="Build endurance and strength for Hyrox", priority=1)
create_goal(mo, "Run 10k under 55 minutes", description="Improve running pace and aerobic capacity", priority=2)

create_measurement(mo, weight=75, body_fat=16, resting_heart_rate=58, notes="Current baseline")

create_fact(mo, "sport", "Hyrox and strength training")
create_fact(mo, "training_time", "prefers afternoon workouts")
create_fact(mo, "experience", "intermediate, 2 years training")

w3 = create_workout(mo, workout_type="Hyrox", duration=70, calories=550, notes="Good conditioning session")
create_exercise(w3, "Sled Push", sets=4, reps=1, weight=100, rir=2)
create_exercise(w3, "Ski Erg", sets=3, reps=1, weight=0, rir=2)

print("Seeded Youssef (id", y, "), Michael (id", m, "), and Mohamed (id", mo, ")")



def seed_conversation(conversation_id, messages, user_id):
    for role, message in messages:
        add_message(conversation_id, role, message, user_id)


# ==========================================================
# YOUSSEF — 8 CONVERSATIONS — user_id = 1
# ==========================================================

seed_conversation("youssef_conv_01", [
    ("user", "What are my current goals?"),
    ("assistant", "You currently have two active goals: finish a Hyrox in under 70 minutes and bench press 100kg."),
], 1)

seed_conversation("youssef_conv_02", [
    ("user", "How much do I currently weigh?"),
    ("assistant", '{"tool":"get_latest_measurement","args":{"user_id":1}}'),
    ("assistant", "Your latest recorded weight is 78 kg with approximately 14% body fat."),
], 1)

seed_conversation("youssef_conv_03", [
    ("user", "What sports do I usually do?"),
    ("assistant", "You do Hyrox and water polo."),
], 1)

seed_conversation("youssef_conv_04", [
    ("user", "When do I prefer to train?"),
    ("assistant", "You prefer morning workouts."),
], 1)

seed_conversation("youssef_conv_05", [
    ("user", "Do I have any injuries?"),
    ("assistant", '{"tool":"get_active_injuries","args":{"user_id":1}}'),
    ("assistant", "You currently have a mild left knee injury described as patellar tendinitis."),
], 1)

seed_conversation("youssef_conv_06", [
    ("user", "What did I do in my last push workout?"),
    ("assistant", '{"tool":"get_latest_workout","args":{"user_id":1}}'),
    ("assistant", "Your latest push workout lasted 60 minutes and included bench press and overhead press. You recorded 4 sets of 8 bench presses at 85 kg and 3 sets of 10 overhead presses at 50 kg."),
], 1)

seed_conversation("youssef_conv_07", [
    ("user", "I want to improve my Hyrox time."),
    ("assistant", "Your main performance goal is to finish Hyrox in under 70 minutes. Since you're an advanced athlete with five years of training experience, we can focus on improving your running efficiency, strength endurance, and transitions."),
], 1)

seed_conversation("youssef_conv_08", [
    ("user", "Should I train in the morning tomorrow?"),
    ("assistant", "Morning training fits your usual preference. Your training schedule can be planned around your Hyrox goal while keeping your current knee issue in mind."),
], 1)


# ==========================================================
# MICHAEL — 8 CONVERSATIONS — user_id = 2
# ==========================================================

seed_conversation("michael_conv_01", [
    ("user", "What are my current goals?"),
    ("assistant", "You have two main goals: lose 8 kg, going from 90 kg to 82 kg, and eventually run 5 km without stopping."),
], 2)

seed_conversation("michael_conv_02", [
    ("user", "How much do I weigh?"),
    ("assistant", '{"tool":"get_latest_measurement","args":{"user_id":2}}'),
    ("assistant", "Your latest recorded weight is 90 kg and your recorded body fat is 24%."),
], 2)

seed_conversation("michael_conv_03", [
    ("user", "I'm new to fitness. What should I focus on?"),
    ("assistant", "Since you're a beginner, focus on building consistency, learning exercise technique, and gradually improving your cardiovascular fitness rather than rushing progression."),
], 2)

seed_conversation("michael_conv_04", [
    ("user", "When do I usually like to work out?"),
    ("assistant", "You prefer evening workouts."),
], 2)

seed_conversation("michael_conv_05", [
    ("user", "Do I have any injuries?"),
    ("assistant", '{"tool":"get_active_injuries","args":{"user_id":2}}'),
    ("assistant", "You have occasional mild lower-back stiffness associated with desk work."),
], 2)

seed_conversation("michael_conv_06", [
    ("user", "What did I do in my first proper workout?"),
    ("assistant", '{"tool":"get_latest_workout","args":{"user_id":2}}'),
    ("assistant", "Your first recorded proper session was a 45-minute full-body workout with approximately 300 calories burned. You performed goblet squats for 3 sets of 12 at 20 kg."),
], 2)

seed_conversation("michael_conv_07", [
    ("user", "I want to lose weight but I'm not very fit."),
    ("assistant", "Your current goal is to move from 90 kg toward 82 kg while building your fitness gradually. Consistency with training and sustainable nutrition will be more important than trying to progress too quickly."),
], 2)

seed_conversation("michael_conv_08", [
    ("user", "Can you help me start running?"),
    ("assistant", "Yes. Your goal is to eventually run 5 km without stopping. We can start with short run-walk sessions and gradually increase the running portions as your fitness improves."),
], 2)


# ==========================================================
# MOHAMED — 8 CONVERSATIONS — user_id = 3
# ==========================================================

seed_conversation("mohamed_conv_01", [
    ("user", "What are my current goals?"),
    ("assistant", "Your main goals are to improve your Hyrox performance and run 10 km in under 55 minutes."),
], 3)

seed_conversation("mohamed_conv_02", [
    ("user", "What is my current weight?"),
    ("assistant", '{"tool":"get_latest_measurement","args":{"user_id":3}}'),
    ("assistant", "Your latest recorded weight is 75 kg with approximately 16% body fat."),
], 3)

seed_conversation("mohamed_conv_03", [
    ("user", "What kind of training do I normally do?"),
    ("assistant", "You mainly do Hyrox and strength training."),
], 3)

seed_conversation("mohamed_conv_04", [
    ("user", "When do I prefer to train?"),
    ("assistant", "You prefer afternoon workouts."),
], 3)

seed_conversation("mohamed_conv_05", [
    ("user", "How experienced am I with training?"),
    ("assistant", "You're an intermediate trainee with around two years of training experience."),
], 3)

seed_conversation("mohamed_conv_06", [
    ("user", "What was my last workout?"),
    ("assistant", '{"tool":"get_latest_workout","args":{"user_id":3}}'),
    ("assistant", "Your latest recorded workout was a 70-minute Hyrox session with approximately 550 calories burned. It included sled pushes and SkiErg work."),
], 3)

seed_conversation("mohamed_conv_07", [
    ("user", "I want to get faster at running."),
    ("assistant", "Your current running goal is to complete 10 km in under 55 minutes. We can work on your aerobic base, pacing, and gradually introduce faster running."),
], 3)

seed_conversation("mohamed_conv_08", [
    ("user", "How can I improve my Hyrox performance?"),
    ("assistant", "Your Hyrox goal is to improve overall performance. We can focus on combining running with strength-endurance work such as sled pushes and SkiErg while improving your transitions between stations."),
], 3)


print("Seeded 8 conversations for Youssef, Michael, and Mohamed.")