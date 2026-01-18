
import sys
sys.path.append('.')

from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

print("Checking MongoDB Data...")
print("=" * 60)

client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DB_NAME')]

print("\nCollections in database:")
for col_name in db.list_collection_names():
    count = db[col_name].count_documents({})
    print(f"  * {col_name}: {count} documents")

print("\nAll Researchers:")
researchers = db.researchers.find()
for researcher in researchers:
    print(f"  * ID: {researcher.get('_id')}")
    print(f"    Name: {researcher.get('name')}")
    print(f"    Email: {researcher.get('email')}")
    print(f"    Department: {researcher.get('department')}")
    print(f"    Role: {researcher.get('role')}")
    print()

print("\nAll Projects:")
projects = db.projects.find()
for project in projects:
    print(f"  * Title: {project.get('title')}")
    print(f"    ID: {project.get('_id')}")
    print(f"    Creator: {project.get('creator_name')}")
    print(f"    Status: {project.get('status')}")
    print()

print("\nAll Publications:")
publications = db.publications.find()
for pub in publications:
    print(f"  * Title: {pub.get('title')}")
    print(f"    ID: {pub.get('_id')}")
    print(f"    Year: {pub.get('year')}")
    print(f"    Journal: {pub.get('journal', 'N/A')}")
    print()

print("=" * 60)
print("MongoDB Data Check Complete")