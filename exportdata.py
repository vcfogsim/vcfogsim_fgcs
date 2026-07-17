import json
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('localhost', 27017)

# Access the database and collection
db = client['EUA_db']
collection = db['servers_data']

# Fetch all documents
documents = list(collection.find())

# Optional: convert ObjectId to string for JSON serialization
for doc in documents:
    doc['_id'] = str(doc['_id'])

# Write to JSON file
with open('servers_data_export.json', 'w', encoding='utf-8') as f:
    json.dump(documents, f, indent=4, ensure_ascii=False)

print("Export complete. Data saved to 'servers_data_export.json'.")

collection = db['events_data']

# Fetch all documents
documents = list(collection.find())

# Optional: convert ObjectId to string for JSON serialization
for doc in documents:
    doc['_id'] = str(doc['_id'])

# Write to JSON file
with open('jobs_data_export.json', 'w', encoding='utf-8') as f:
    json.dump(documents, f, indent=4, ensure_ascii=False)

print("Export complete. Data saved to 'jobs_data_export.json'.")