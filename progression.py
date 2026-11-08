LEVELS=['A1','A2','B1','B2','C1','C2']
def rank(level):return LEVELS.index(level) if level in LEVELS else 0
def allowed(user,level):return user['role']=='teacher' or rank(level)<=rank(user['level'])
def available_levels(user):return LEVELS if user['role']=='teacher' else LEVELS[:rank(user['level'])+1]
