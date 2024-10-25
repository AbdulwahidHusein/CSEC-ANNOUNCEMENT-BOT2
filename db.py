from pymongo import MongoClient
from config import MONGO_CONNECTION_STRING

client = MongoClient(MONGO_CONNECTION_STRING)
# db = client["csec-updater-secondyr"]
db = client["csec-updater-firstyr"]
# Collections
groups_collection = db["groups"]
admin_collection = db["admins"]
state_collection = db["state"]

ready_messagesids_collection = db["ready_messages"]

# def initialize_db(bot_number):
#     global groups_collection, admin_collection, state_collection
#     groups_collection = db[f"groups_{bot_number}"]
#     admin_collection = db[f"admins_{bot_number}"]
#     state_collection = db[f"state_{bot_number}"]

def add_to_readymessageids(user_id, message_id):
    """
    Adds a message ID to the user's list of ready message IDs.
    If the user does not exist, it creates a new document.
    """
    ready_messagesids_collection.update_one(
        {"user_id": user_id},
        {"$addToSet": {"message_ids": message_id}},
        upsert=True
    )

def get_message_ids_by_user_id(user_id):
    """
    Retrieves the list of message IDs for the specified user_id.
    Returns an empty list if the user does not exist.
    """
    user_data = ready_messagesids_collection.find_one({"user_id": user_id}, {"message_ids": 1})
    return user_data["message_ids"] if user_data else []

def delete_user_messages(user_id):
    """
    Deletes the entire document for the specified user.
    """
    ready_messagesids_collection.delete_one({"user_id": user_id})
    
# Group management 

def add_group(group: dict):   
    data = {
        "id": group['id'], 
        "title": group['title'],
        "username": group.get('username', None)  
    }
    groups_collection.update_one({"id": group['id']}, {"$set": data}, upsert=True)
    
def remove_group(group_id):
    groups_collection.delete_one({"id": group_id})
    
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

def update_admin_info(user_info):
    admin_data = None
    admin_data =find_admin_by_username(user_info.get("username"))
    if admin_data:
        #update it
        admin_data["id"] = user_info["id"]
        admin_data['first_name'] = user_info.get('first_name')
        admin_data['last_name'] = user_info.get('last_name')
        admin_collection.update_one({"username": user_info.get("username")}, {"$set": admin_data})

# State management
def set_user_state(user_id, state):
    state_collection.update_one({"user_id": user_id}, {"$set": {"state": state}}, upsert=True)

def get_user_state(user_id):
    return state_collection.find_one({"user_id": user_id})

def delete_user_state(user_id):
    state_collection.delete_one({"user_id": user_id})
