from pymongo import MongoClient
from bson import ObjectId


def connect_to_mongo(host: str, port: str, database_name: str) -> MongoClient:
    client = MongoClient(host, int(port))
    return client[database_name]


def update_passwords(db: str, new_password_hash: str) -> int:
    result = db.Usuario.update_many({}, {"$set": {"Password": new_password_hash}})
    return result.matched_count


def find_admin_emails(db: MongoClient) -> list:
    query = {"IsApproved": True, "IsLockedOut": False, "Roles": "administrador"}
    projection = {"Email": 1, "_id": 0}
    return [doc["Email"] for doc in db.Usuario.find(query, projection)]
