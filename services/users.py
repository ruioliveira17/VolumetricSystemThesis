import os
import json

USER_FILE = "auth/users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
    with open(USER_FILE, "r") as f:
        return json.load(f)
    
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)