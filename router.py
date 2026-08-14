from memory.manager import create_goal,create_injury,create_user,create_fact,get_active_goals,get_all_injuries


#create_fact(1, "sport", "Hyrox and water polo")
#create_injury(1, body_part="knee", description="mild left knee soreness", severity="mild")
print(get_all_injuries(1))
print(get_active_goals(1))