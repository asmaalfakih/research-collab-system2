#!/usr/bin/env python3
"""
Complete System Initialization
Run this once to set up everything
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import bcrypt

sys.path.append(str(Path(__file__).parent))

from colorama import init, Fore, Style

init(autoreset=True)

print(f"{Fore.CYAN}{'=' * 70}")
print(f"{Fore.YELLOW} RESEARCH COLLABORATION SYSTEM - INITIALIZATION")
print(f"{Fore.CYAN}{'=' * 70}")


def print_step(step_num, description):
    print(f"\n{Fore.YELLOW}{step_num}. {description}")
    print(f"{Fore.CYAN}{'-' * 50}")


# Step 1: Initialize MongoDB
print_step("1", "Initializing MongoDB Database")
try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from dotenv import load_dotenv

    load_dotenv()

    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('MONGODB_DB_NAME')]

    print(f"{Fore.WHITE}   Database: {db.name}")

    # Create collections if they don't exist
    collections = ['researchers', 'projects', 'publications', 'admins', 'logs']
    for collection in collections:
        if collection not in db.list_collection_names():
            db.create_collection(collection)
            print(f"{Fore.GREEN}   Created collection: {collection}")

    # Create indexes
    db.researchers.create_index([('email', ASCENDING)], unique=True, name='email_unique')
    db.researchers.create_index([('profile_status', ASCENDING)], name='status_idx')
    print(f"{Fore.GREEN}   Created indexes")

    # Create admin user
    admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_data = {
        'name': 'System Admin',
        'email': 'admin@university.edu',
        'password': admin_password,
        'department': 'Administration',
        'profile_status': 'approved',
        'role': 'admin',
        'research_interests': ['System Management'],
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'login_count': 0
    }

    # Check if admin exists
    existing = db.researchers.find_one({'email': 'admin@university.edu'})
    if not existing:
        db.researchers.insert_one(admin_data)
        print(f"{Fore.GREEN}   Created admin: admin@university.edu / admin123")
    else:
        print(f"{Fore.YELLOW}   Admin already exists")

    print(f"{Fore.GREEN} MongoDB initialization completed")

except Exception as e:
    print(f"{Fore.RED} MongoDB Error: {e}")

# Step 2: Initialize Neo4j
print_step("2", "Initializing Neo4j Graph Database")
try:
    from neo4j import GraphDatabase
    from dotenv import load_dotenv

    load_dotenv()

    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )

    with driver.session() as session:
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT researcher_id_unique IF NOT EXISTS FOR (r:Researcher) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT researcher_email_unique IF NOT EXISTS FOR (r:Researcher) REQUIRE r.email IS UNIQUE"
        ]

        for constraint in constraints:
            try:
                session.run(constraint)
                print(f"{Fore.GREEN}   Created constraint")
            except Exception as e:
                print(f"{Fore.YELLOW}   Constraint may already exist: {e}")

        # Create admin node
        result = session.run("""
            MERGE (r:Researcher {email: $email})
            SET r.id = $id,
                r.name = $name,
                r.department = $department,
                r.profile_status = $status,
                r.created_at = datetime()
            RETURN r.name
        """, {
            'email': 'admin@university.edu',
            'id': 'admin_001',
            'name': 'System Admin',
            'department': 'Administration',
            'status': 'approved'
        })

        if result.single():
            print(f"{Fore.GREEN}   Created admin node in Neo4j")

    driver.close()
    print(f"{Fore.GREEN} Neo4j initialization completed")

except Exception as e:
    print(f"{Fore.RED} Neo4j Error: {e}")

# Step 3: Initialize Redis
print_step("3", "Initializing Redis Cache")
try:
    import redis
    from dotenv import load_dotenv

    load_dotenv()

    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT')),
        password=os.getenv('REDIS_PASSWORD'),
        ssl=os.getenv('REDIS_SSL', 'False').lower() == 'true',
        decode_responses=True
    )

    if r.ping():
        # Set system info
        r.set("system:name", "Research Collaboration System")
        r.set("system:initialized", datetime.utcnow().isoformat())
        r.set("system:version", "1.0.0")

        print(f"{Fore.GREEN}   Redis connected and initialized")
        print(f"{Fore.WHITE}   Host: {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}")
        print(f"{Fore.WHITE}   Keys set: {r.keys('system:*')}")
    else:
        print(f"{Fore.RED}   Redis ping failed")

except Exception as e:
    print(f"{Fore.RED} Redis Error: {e}")

print(f"\n{Fore.CYAN}{'=' * 70}")
print(f"{Fore.GREEN} SYSTEM INITIALIZATION COMPLETED!")
print(f"\n{Fore.YELLOW} Next steps:")
print(f"{Fore.WHITE}   1. Run sample data: python scripts/sample_data.py")
print(f"{Fore.WHITE}   2. Start main system: python run.py")
print(f"{Fore.WHITE}   3. Test admin: python run.py admin")
print(f"{Fore.CYAN}{'=' * 70}")