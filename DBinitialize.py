 #1. Does the code import + DB initialize?
from memory.database import initialize_database
initialize_database()          # creates memory.db if missing

# 2. Do the exact functions the executor needs exist?
from memory.manager import (
    get_active_goals, get_latest_measurement, get_active_injuries,
    get_workouts, get_fact, get_user,
    create_user, create_goal,
)
print("all manager functions present")

# 3. Seed it
create_user("Youssef")
create_goal(1, "Sub-70 Hyrox")

# 4. Read it back
print(get_active_goals(1))