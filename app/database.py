import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
db = client[os.getenv("DB_NAME")]

# Collections — one per data type
threads_collection = db["threads"]
messages_collection = db["chat_messages"]
users_collection = db["users"]
chunks_collection = db["document_chunks"]