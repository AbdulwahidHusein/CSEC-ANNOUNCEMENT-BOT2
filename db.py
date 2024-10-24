from pymongo import MongoClient
from config import MONGO_CONNECTION_STRING

client = MongoClient(MONGO_CONNECTION_STRING)
db = client["csec-updater"]

# Collections
groups_collection = db["groups"]
admin_collection = db["admins"]
state_collection = db["state"] 

# Group management 

def add_group(group: dict):   
    data = {
        "id": group['id'], 
        "title": group['title'],
        "username": group.get('username', None)  
    }
    groups_collection.update_one({"id": group['id']}, {"$set": data}, upsert=True)
    
def load_groups():
    return list(groups_collection.find({}))

def save_group(group):
    groups_collection.update_one({"id": group["id"]}, {"$set": group}, upsert=True)

# Admin management
def find_admin_by_id(user_id):
    return admin_collection.find_one({"id": user_id})

def find_admin_by_username(username):
    return admin_collection.find_one({"username": username})

def add_admin(admin_data):
    admin_collection.insert_one(admin_data)

def is_admin_exists(admin_data):
    return admin_collection.find_one({"$and": [{"id": admin_data["id"]}, {"username": admin_data["username"]}]})

def get_admins():
    return list(admin_collection.find({}))

# State management
def set_user_state(user_id, state):
    state_collection.update_one({"user_id": user_id}, {"$set": {"state": state}}, upsert=True)

def get_user_state(user_id):
    return state_collection.find_one({"user_id": user_id})

def delete_user_state(user_id):
    state_collection.delete_one({"user_id": user_id})
