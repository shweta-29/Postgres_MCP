"""
seed_db.py
Populate MongoDB with dummy data for testing
"""

from pymongo import MongoClient
import config

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]

# Clear old data
db.customers.delete_many({})

# Insert dummy customers
db.customers.insert_many([
    {"name": "Alice", "city": "London", "age": 30},
    {"name": "Bob", "city": "Paris", "age": 25},
    {"name": "Charlie", "city": "London", "age": 35},
    {"name": "Diana", "city": "Berlin", "age": 28},
])

print("Dummy data inserted.")
