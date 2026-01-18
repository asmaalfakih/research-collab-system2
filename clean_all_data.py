
import sys
import os
from pathlib import Path
from colorama import init, Fore, Style

sys.path.append(str(Path(__file__).parent))

init(autoreset=True)

print(f"{Fore.RED}{'=' * 70}")
print(f"{Fore.YELLOW} CLEANING ALL DATA FROM ALL DATABASES")
print(f"{Fore.RED}{'=' * 70}")

print(f"\n{Fore.YELLOW} This will delete ALL data from:")
print(f"{Fore.WHITE}   * MongoDB: All researchers, projects, publications")
print(f"{Fore.WHITE}   * Neo4j: All nodes and relationships")
print(f"{Fore.WHITE}   * Redis: All cached data")

confirm = input(f"\n{Fore.RED} Type 'DELETE_ALL' to confirm: ")

if confirm != 'DELETE_ALL':
    print(f"\n{Fore.YELLOW} Operation cancelled")
    sys.exit(0)

print(f"\n{Fore.YELLOW} Cleaning data...")

print(f"\n{Fore.YELLOW}1. Cleaning MongoDB...")
try:
    from pymongo import MongoClient
    from dotenv import load_dotenv

    load_dotenv()

    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('MONGODB_DB_NAME')]

    collections = ['researchers', 'projects', 'publications', 'logs']
    for collection in collections:
        if collection in db.list_collection_names():
            result = db[collection].delete_many({})
            print(f"{Fore.GREEN}   MongoDB {collection}: deleted {result.deleted_count} documents")

    print(f"{Fore.GREEN} MongoDB cleaned successfully")

except Exception as e:
    print(f"{Fore.RED} MongoDB error: {e}")

print(f"\n{Fore.YELLOW}2. Cleaning Neo4j...")
try:
    from neo4j import GraphDatabase
    from dotenv import load_dotenv

    load_dotenv()

    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )

    with driver.session() as session:
        result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
        count = result.single()["deleted"]
        print(f"{Fore.GREEN}   Neo4j: deleted {count} nodes")

    driver.close()
    print(f"{Fore.GREEN} Neo4j cleaned successfully")

except Exception as e:
    print(f"{Fore.RED} Neo4j error: {e}")

print(f"\n{Fore.YELLOW}3. Cleaning Redis...")
try:
    import redis
    from dotenv import load_dotenv

    load_dotenv()

    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT')),
        password=os.getenv('REDIS_PASSWORD'),
        ssl=False,
        decode_responses=True
    )

    if r.ping():
        keys = r.keys("*")
        if keys:
            r.delete(*keys)
            print(f"{Fore.GREEN}   Redis: deleted {len(keys)} keys")
        else:
            print(f"{Fore.YELLOW}   Redis: no keys found")

        print(f"{Fore.GREEN} Redis cleaned successfully")
    else:
        print(f"{Fore.RED}   Redis not connected")

except Exception as e:
    print(f"{Fore.RED} Redis error: {e}")

print(f"\n{Fore.GREEN}{'=' * 70}")
print(f"{Fore.GREEN} ALL DATA CLEANED SUCCESSFULLY!")
print(f"{Fore.GREEN} Now you can run: python scripts/sample_data.py")
print(f"{Fore.GREEN}{'=' * 70}")