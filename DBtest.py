from memory.database import initialize_database
from memory.manager import *

initialize_database()

from memory.database import initialize_database
from memory.manager import create_user, create_goal, create_fact, create_measurement

initialize_database()  # creates tables if they don't exist

uid = create_user("Test User", age=22, sex="M", height=180)
create_goal(uid, "Lose weight", target_date="2026-05-01")
create_fact(uid, "occupation", "student")
create_fact(uid, "hates", "burpees")
create_measurement(uid, weight=82.5, resting_heart_rate=60)

print("Seeded user id:", uid)  # should print 1 on a fresh database

#print(get_user(user_id))

#print(get_all_users())