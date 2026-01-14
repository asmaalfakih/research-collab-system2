#!/usr/bin/env python3
"""
Test all database connections
"""

import sys
import os
from pathlib import Path
from colorama import init, Fore, Style

sys.path.append(str(Path(__file__).parent))

init(autoreset=True)

print(f"{Fore.CYAN}{'=' * 60}")
print(f"{Fore.YELLOW} TESTING DATABASE CONNECTIONS")
print(f"{Fore.CYAN}{'=' * 60}")

# Test MongoDB
print(f"\n{Fore.YELLOW}1. Testing MongoDB Connection...")
try:
    from pymongo import MongoClient
    from dotenv import load_dotenv

    load_dotenv()

    client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[os.getenv('MONGODB_DB_NAME')]

    print(f"{Fore.GREEN}   MongoDB Connected!")
    print(f"{Fore.WHITE}   Database: {db.name}")
    print(f"{Fore.WHITE}   Collections: {db.list_collection_names()}")

except Exception as e:
    print(f"{Fore.RED}   MongoDB Error: {e}")

# Test Neo4j
print(f"\n{Fore.YELLOW}2. Testing Neo4j Connection...")
try:
    from neo4j import GraphDatabase
    from dotenv import load_dotenv

    load_dotenv()

    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD')),
        connection_timeout=5
    )

    with driver.session() as session:
        result = session.run("RETURN 'Connected!' as message")
        print(f"{Fore.GREEN}   Neo4j Connected!")

    driver.close()

except Exception as e:
    print(f"{Fore.RED}   Neo4j Error: {e}")

# Test Redis
print(f"\n{Fore.YELLOW}3. Testing Redis Connection...")
try:
    import redis
    from dotenv import load_dotenv

    load_dotenv()

    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT')),
        password=os.getenv('REDIS_PASSWORD'),
        ssl=os.getenv('REDIS_SSL', 'False').lower() == 'true',
        decode_responses=True,
        socket_timeout=5
    )

    if r.ping():
        print(f"{Fore.GREEN}   Redis Connected!")
        print(f"{Fore.WHITE}   Host: {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}")
    else:
        print(f"{Fore.RED}   Redis Ping Failed")

except Exception as e:
    print(f"{Fore.RED}   Redis Error: {e}")

print(f"\n{Fore.CYAN}{'=' * 60}")
print(f"{Fore.GREEN} CONNECTION TEST COMPLETED")
print(f"{Fore.CYAN}{'=' * 60}")