import pandas as pd

class Skill:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return self.name
    
class Role: 
    def __init__(self, name):
        self.name = name
        self.skills = {}

    def add_skill(self, skill, required_level):
        self.skills[skill] = required_level

    def __repr__(self):
        skills_list = ', '.join([f"{skill} (Level {level})" for skill, level in self.skills.items()])
        return f"Role: {self.name}, Required Skills: {skills_list}"
    
class User:
    def __init__(self, name):
        self.name = name
        self.skills = {}

    def assess_skill(self, skill, level):
        self.skills[skill] = level
    
    def __repr__(self):
        skills_list = ', '.join([f"{skill} (Level {level})" for skill, level in self.skills.items()])


class Assessment: 
    @staticmethod
    def evaluate(user, role):
        strengths = {}
        gaps = {}
        for skill, required_level in role.skills.items():
            user_level = user.skills.get(skill, 0)
            if user_level >= required_level:
                strengths[skill] = user_level
            else: 
                gaps[skill] = (user_level, required_level)
        return strengths, gaps
    
class Visualisation:
    @staticmethod
    def display(strengths, gaps):
        print("Strengths: ")
        for skill, level in strengths.items():
            print(f"{skill}: Level {level}")

        print("\nGaps:")
        for skill, (user_level, required_level) in gaps.items():
            print(f"{skill}: Level {user_level} (required: Level {required_level})")

def load_data(file_path):
    df = pd.read_csv(file_path)
    roles = {}
    users = {}

    for _, row in df.iterrows():
        if row['Type'] == 'role':
            role_name = row['Name']
            if role_name not in roles:
                roles[role_name] = Role(role_name)
            roles[role_name].add_skill(row['Skill'], row['Level'])
        elif row['Type'] == 'user':
            user_name = row['Name'] 
            if user_name not in users:
                users[user_name] = User(user_name) 
            users[user_name].assess_skill(row['Skill'], row['Level'])
                                          
    return roles, users

file_path = 'ld_team_skills.csv'  # Replace with the path to your CSV file
roles, users = load_data(file_path)

# Let's assume we want to evaluate Alice against the L&D Manager role
role_name = input('Enter the Role name: ')
user_name = input('Enter the User name: ')

role = roles.get(role_name)
user = users.get(user_name)

if role and user:
    strengths, gaps = Assessment.evaluate(user, role)
    Visualisation.display(strengths, gaps)
else:
    print("Role or user not found.")