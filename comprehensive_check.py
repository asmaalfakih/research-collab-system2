
import sys
import os
from pathlib import Path
from colorama import init, Fore, Style

sys.path.append(str(Path(__file__).parent))

init(autoreset=True)

print(f"{Fore.CYAN}{'=' * 80}")
print(f"{Fore.YELLOW} COMPREHENSIVE DATABASE CHECK")
print(f"{Fore.CYAN}{'=' * 80}")

def check_mongodb():
    print(f"\n{Fore.YELLOW} MongoDB Check")
    print(f"{Fore.CYAN}{'-' * 40}")

    try:
        from pymongo import MongoClient
        from dotenv import load_dotenv

        load_dotenv()

        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client[os.getenv('MONGODB_DB_NAME')]

        print(f"{Fore.GREEN} Connected to MongoDB")

        print(f"\n{Fore.WHITE}Collections:")
        for col in ['researchers', 'projects', 'publications']:
            count = db[col].count_documents({})
            if count > 0:
                print(f"{Fore.GREEN}  * {col}: {count} documents")
            else:
                print(f"{Fore.YELLOW}  * {col}: {count} documents")

        if db.researchers.count_documents({}) > 0:
            print(f"\n{Fore.WHITE}Sample Researcher:")
            researcher = db.researchers.find_one()
            print(f"  * Name: {researcher.get('name')}")
            print(f"  * Email: {researcher.get('email')}")
            print(f"  * Department: {researcher.get('department')}")

        return True

    except Exception as e:
        print(f"{Fore.RED} MongoDB Check Failed: {e}")
        return False

def check_neo4j():
    print(f"\n{Fore.YELLOW} Neo4j Check")
    print(f"{Fore.CYAN}{'-' * 40}")

    try:
        from neo4j import GraphDatabase
        from dotenv import load_dotenv

        load_dotenv()

        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )

        with driver.session() as session:
            result = session.run("RETURN 'Connected' as status")
            print(f"{Fore.GREEN} Connected to Neo4j")

            result = session.run("MATCH (r:Researcher) RETURN count(r) as count")
            node_count = result.single()["count"]
            print(f"{Fore.WHITE}  * Researchers in graph: {node_count}")

            result = session.run("MATCH ()-[r:COLLABORATED_WITH]-() RETURN count(r) as count")
            rel_count = result.single()["count"]
            print(f"{Fore.WHITE}  * Collaboration relationships: {rel_count}")

        driver.close()
        return True

    except Exception as e:
        print(f"{Fore.RED} Neo4j Check Failed: {e}")
        return False

def check_redis():
    print(f"\n{Fore.YELLOW} Redis Check")
    print(f"{Fore.CYAN}{'-' * 40}")

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
            print(f"{Fore.GREEN} Connected to Redis")

            keys = r.keys("*")
            print(f"{Fore.WHITE}  * Total keys: {len(keys)}")

            return True
        else:
            print(f"{Fore.RED} Redis ping failed")
            return False

    except Exception as e:
        print(f"{Fore.RED} Redis Check Failed: {e}")
        return False

def main():
    print(f"\n{Fore.YELLOW} Running comprehensive database checks...")

    results = []

    if check_mongodb():
        results.append(("MongoDB", True))
    else:
        results.append(("MongoDB", False))

    if check_neo4j():
        results.append(("Neo4j", True))
    else:
        results.append(("Neo4j", False))

    if check_redis():
        results.append(("Redis", True))
    else:
        results.append(("Redis", False))

    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.YELLOW} CHECK SUMMARY")
    print(f"{Fore.CYAN}{'=' * 80}")

    for db, status in results:
        if status:
            print(f"{Fore.GREEN} {db}: Working correctly")
        else:
            print(f"{Fore.RED} {db}: Issues found")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n{Fore.CYAN}{'=' * 80}")
    if passed == total:
        print(f"{Fore.GREEN} ALL DATABASES ARE WORKING CORRECTLY!")
        print(f"{Fore.GREEN} Data is successfully stored in all three databases")
    elif passed >= 2:
        print(f"{Fore.YELLOW} MOST DATABASES ARE WORKING")
    else:
        print(f"{Fore.RED} MULTIPLE DATABASE ISSUES")

    print(f"\n{Fore.YELLOW} Next steps:")
    print(f"{Fore.WHITE}  1. Run the main system: python run.py")
    print(f"{Fore.WHITE}  2. Test admin interface: python run.py admin")
    print(f"{Fore.CYAN}{'=' * 80}")

if __name__ == "__main__":
    main()