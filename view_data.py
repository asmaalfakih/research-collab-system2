
import sys
import os
from pathlib import Path
from colorama import init, Fore, Style
from tabulate import tabulate
import json

BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

init(autoreset=True)

def display_header(title):
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.YELLOW}{title}")
    print(f"{Fore.CYAN}{'=' * 80}")

def check_database_connections():
    print(f"\n{Fore.YELLOW}Checking Database Connections...")

    results = {}

    try:
        from pymongo import MongoClient
        from dotenv import load_dotenv
        load_dotenv()

        client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
        db_name = os.getenv('MONGODB_DB_NAME', 'research_collab_db')
        db = client[db_name]
        client.admin.command('ping')

        results['mongodb'] = {
            'status': 'connected',
            'db': db,
            'client': client
        }
        print(f"{Fore.GREEN}MongoDB: Connected to '{db_name}'")
    except Exception as e:
        results['mongodb'] = {'status': 'error', 'error': str(e)}
        print(f"{Fore.RED}MongoDB: {e}")

    try:
        from neo4j import GraphDatabase
        from dotenv import load_dotenv
        load_dotenv()

        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            auth=(
                os.getenv('NEO4J_USERNAME', 'neo4j'),
                os.getenv('NEO4J_PASSWORD', 'research123')
            )
        )

        with driver.session() as session:
            session.run("RETURN 1")
            results['neo4j'] = {
                'status': 'connected',
                'driver': driver
            }
            print(f"{Fore.GREEN}Neo4j: Connected")
    except Exception as e:
        results['neo4j'] = {'status': 'error', 'error': str(e)}
        print(f"{Fore.RED}Neo4j: {e}")

    try:
        import redis
        from dotenv import load_dotenv
        load_dotenv()

        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            ssl=False,
            decode_responses=True,
            socket_timeout=5
        )

        if r.ping():
            results['redis'] = {
                'status': 'connected',
                'client': r
            }
            print(f"{Fore.GREEN}Redis: Connected")
        else:
            results['redis'] = {'status': 'error', 'error': 'Ping failed'}
            print(f"{Fore.RED}Redis: Ping failed")
    except Exception as e:
        results['redis'] = {'status': 'error', 'error': str(e)}
        print(f"{Fore.YELLOW}Redis: {e}")

    return results

def show_mongodb_data(db):
    display_header("MONGODB DATA - RESEARCHERS, PROJECTS, PUBLICATIONS")

    researchers = list(db.researchers.find().sort('created_at', -1).limit(20))
    print(f"\n{Fore.GREEN}RESEARCHERS ({len(researchers)} documents):")

    if researchers:
        table_data = []
        for i, researcher in enumerate(researchers, 1):
            created = researcher.get('created_at', '')
            created_str = created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else str(created)[:10]

            table_data.append([
                i,
                researcher.get('name', 'N/A'),
                researcher.get('email', 'N/A'),
                researcher.get('department', 'N/A'),
                researcher.get('profile_status', 'N/A'),
                len(researcher.get('research_interests', [])),
                created_str
            ])

        headers = ['No', 'Name', 'Email', 'Department', 'Status', 'Interests', 'Created']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))
    else:
        print(f"{Fore.YELLOW}No researchers found")

    projects = list(db.projects.find().sort('created_at', -1).limit(10))
    print(f"\n{Fore.GREEN}PROJECTS ({len(projects)} documents):")

    if projects:
        table_data = []
        for i, project in enumerate(projects, 1):
            participants = project.get('participants', [])
            start_date = project.get('start_date', 'N/A')

            table_data.append([
                i,
                project.get('title', 'N/A'),
                project.get('creator_name', 'N/A'),
                project.get('status', 'N/A'),
                len(participants) if isinstance(participants, list) else 0,
                str(start_date)[:10] if start_date else 'N/A',
                project.get('research_area', 'N/A')
            ])

        headers = ['No', 'Title', 'Creator', 'Status', 'Participants', 'Start Date', 'Research Area']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))
    else:
        print(f"{Fore.YELLOW}No projects found")

    publications = list(db.publications.find().sort('year', -1).limit(10))
    print(f"\n{Fore.GREEN}PUBLICATIONS ({len(publications)} documents):")

    if publications:
        table_data = []
        for i, publication in enumerate(publications, 1):
            authors = publication.get('authors', [])
            author_names = []

            for author in authors[:2]:
                if isinstance(author, dict):
                    author_names.append(author.get('name', 'Unknown'))
                else:
                    author_names.append(str(author))

            if len(authors) > 2:
                author_names.append('...')

            table_data.append([
                i,
                publication.get('title', 'N/A'),
                ', '.join(author_names),
                publication.get('year', 'N/A'),
                publication.get('journal', 'N/A'),
                publication.get('citation_count', 0)
            ])

        headers = ['No', 'Title', 'Authors', 'Year', 'Journal', 'Citations']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))
    else:
        print(f"{Fore.YELLOW}No publications found")

def show_neo4j_data(driver):
    display_header("NEO4J GRAPH DATA - COLLABORATION NETWORK")

    with driver.session() as session:
        result = session.run("MATCH (r:Researcher) RETURN count(r) as count")
        count_record = result.single()
        researcher_count = count_record["count"] if count_record else 0

        print(f"\n{Fore.GREEN}RESEARCHERS IN GRAPH: {researcher_count}")

        if researcher_count > 0:
            result = session.run(
)

            table_data = []
            for i, record in enumerate(result, 1):
                table_data.append([
                    i,
                    record["name"],
                    record["email"],
                    record["department"]
                ])

            if table_data:
                headers = ['No', 'Name', 'Email', 'Department']
                print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        print(f"\n{Fore.GREEN}COLLABORATION RELATIONSHIPS:")
        result = session.run(
)

        table_data = []
        for i, record in enumerate(result, 1):
            first_date = record["first_date"] or "N/A"
            last_date = record["last_date"] or "N/A"

            if hasattr(first_date, 'iso_format'):
                first_date = first_date.iso_format()
            if hasattr(last_date, 'iso_format'):
                last_date = last_date.iso_format()

            table_data.append([
                i,
                record["researcher1"],
                record["researcher2"],
                record["relationship_type"],
                record["count"],
                str(first_date),
                str(last_date)
            ])

        if table_data:
            headers = ['No', 'Researcher 1', 'Researcher 2', 'Type', 'Count', 'First Date', 'Last Date']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))
        else:
            print(f"{Fore.YELLOW}No collaboration relationships found")

        print(f"\n{Fore.GREEN}RELATIONSHIP STATISTICS:")
        result = session.run(
)

        table_data = []
        for i, record in enumerate(result, 1):
            table_data.append([
                i,
                record["relationship_type"],
                record["total_count"],
                f"{record['avg_collaborations']:.1f}",
                record["max_collaborations"]
            ])

        if table_data:
            headers = ['No', 'Type', 'Total', 'Avg Collaborations', 'Max Collaborations']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

def show_redis_data(client):
    display_header("REDIS CACHE DATA")

    try:
        keys = client.keys("*")
        print(f"\n{Fore.GREEN}TOTAL KEYS IN REDIS: {len(keys)}")

        if keys:
            type_counts = {}
            for key in keys[:100]:
                key_type = client.type(key)
                type_counts[key_type] = type_counts.get(key_type, 0) + 1

            print(f"\n{Fore.GREEN}KEY TYPE DISTRIBUTION:")
            table_data = []
            for type_name, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                table_data.append([type_name, count])

            print(tabulate(table_data, headers=['Type', 'Count'], tablefmt='simple_grid'))

            print(f"\n{Fore.GREEN}SAMPLE KEYS (first 20):")
            table_data = []
            for i, key in enumerate(keys[:20], 1):
                key_type = client.type(key)
                ttl = client.ttl(key)

                value_preview = ""
                if key_type == 'string':
                    value = client.get(key)
                    if value and len(value) > 50:
                        value_preview = value[:50] + "..."
                    elif value:
                        value_preview = value

                table_data.append([
                    i,
                    key,
                    key_type,
                    f"{ttl}s" if ttl > 0 else "No TTL",
                    value_preview
                ])

            headers = ['No', 'Key', 'Type', 'TTL', 'Value Preview']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        session_keys = [k for k in keys if k.startswith('session:')] if 'keys' in locals() else []
        print(f"\n{Fore.GREEN}ACTIVE SESSIONS: {len(session_keys)}")

        if session_keys:
            table_data = []
            for i, key in enumerate(session_keys[:5], 1):
                try:
                    session_data = client.get(key)
                    if session_data:
                        data = json.loads(session_data)
                        table_data.append([
                            i,
                            key.replace('session:', ''),
                            data.get('name', 'N/A'),
                            data.get('email', 'N/A'),
                            data.get('role', 'N/A')
                        ])
                except:
                    table_data.append([i, key, 'Error', 'Error', 'Error'])

            if table_data:
                headers = ['No', 'Session ID', 'Name', 'Email', 'Role']
                print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        print(f"\n{Fore.GREEN}REDIS SERVER INFO:")
        try:
            info = client.info()
            stats = [
                ['Redis Version', info.get('redis_version', 'N/A')],
                ['Memory Used', info.get('used_memory_human', 'N/A')],
                ['Connected Clients', info.get('connected_clients', 0)],
                ['Total Commands', info.get('total_commands_processed', 0)],
                ['Keyspace Hits', info.get('keyspace_hits', 0)],
                ['Keyspace Misses', info.get('keyspace_misses', 0)]
            ]

            hit_rate = 0
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            if hits + misses > 0:
                hit_rate = hits / (hits + misses) * 100
            stats.append(['Cache Hit Rate', f"{hit_rate:.1f}%"])

            print(tabulate(stats, headers=['Metric', 'Value'], tablefmt='simple_grid'))
        except:
            print(f"{Fore.YELLOW}Could not retrieve Redis info")

    except Exception as e:
        print(f"{Fore.RED}Error reading Redis data: {e}")

def show_system_integration():
    display_header("SYSTEM INTEGRATION DATA")

    try:
        from app.database.mongodb import mongodb
        from app.database.neo4j import neo4j

        print(f"\n{Fore.GREEN}SYSTEM STATISTICS:")

        stats_data = []

        if hasattr(mongodb, 'db'):
            researcher_count = mongodb.db.researchers.count_documents({})
            project_count = mongodb.db.projects.count_documents({})
            publication_count = mongodb.db.publications.count_documents({})

            stats_data.append(['MongoDB Researchers', researcher_count])
            stats_data.append(['MongoDB Projects', project_count])
            stats_data.append(['MongoDB Publications', publication_count])
        else:
            stats_data.append(['MongoDB', 'Not connected'])

        if hasattr(neo4j, 'driver'):
            try:
                with neo4j.driver.session() as session:
                    result = session.run("MATCH (r:Researcher) RETURN count(r) as count")
                    record = result.single()
                    neo4j_researchers = record["count"] if record else 0

                    result = session.run("MATCH ()-[r]-() RETURN count(r) as count")
                    record = result.single()
                    relationships = record["count"] if record else 0

                    stats_data.append(['Neo4j Researchers', neo4j_researchers])
                    stats_data.append(['Neo4j Relationships', relationships])
            except:
                stats_data.append(['Neo4j', 'Error querying'])
        else:
            stats_data.append(['Neo4j', 'Not connected'])

        print(tabulate(stats_data, headers=['Metric', 'Count'], tablefmt='simple_grid'))

        print(f"\n{Fore.GREEN}COLLABORATION INSIGHTS:")

        if hasattr(neo4j, 'driver') and hasattr(mongodb, 'db'):
            with neo4j.driver.session() as session:
                result = session.run(
)

                insights_data = []
                for i, record in enumerate(result, 1):
                    insights_data.append([
                        i,
                        record["name"],
                        record["relationship_count"],
                        record["total_collaborations"]
                    ])

                if insights_data:
                    headers = ['Rank', 'Researcher', 'Relationships', 'Total Collaborations']
                    print(tabulate(insights_data, headers=headers, tablefmt='simple_grid'))

                result = session.run(
)

                rel_data = []
                for record in result:
                    rel_data.append([record["rel_type"], record["count"]])

                if rel_data:
                    print(f"\n{Fore.GREEN}RELATIONSHIP TYPES:")
                    print(tabulate(rel_data, headers=['Type', 'Count'], tablefmt='simple_grid'))

    except Exception as e:
        print(f"{Fore.YELLOW}Could not generate integration data: {e}")

def main():
    print(f"{Fore.CYAN}{'*' * 100}")
    print(f"{Fore.YELLOW}RESEARCH COLLABORATION SYSTEM - COMPLETE DATA VIEW")
    print(f"{Fore.CYAN}{'*' * 100}")

    try:
        db_results = check_database_connections()

        print(f"\n{Fore.YELLOW}Displaying Data from Connected Databases...")
        print(f"{Fore.CYAN}{'-' * 80}")

        if db_results.get('mongodb', {}).get('status') == 'connected':
            show_mongodb_data(db_results['mongodb']['db'])

        if db_results.get('neo4j', {}).get('status') == 'connected':
            show_neo4j_data(db_results['neo4j']['driver'])

        if db_results.get('redis', {}).get('status') == 'connected':
            show_redis_data(db_results['redis']['client'])

        show_system_integration()

        print(f"\n{Fore.CYAN}{'*' * 100}")
        print(f"{Fore.GREEN}DATA VIEW COMPLETED SUCCESSFULLY")
        print(f"{Fore.CYAN}{'*' * 100}")

        print(f"\n{Fore.YELLOW}SUMMARY:")
        mongodb_status = db_results.get('mongodb', {}).get('status', 'unknown')
        neo4j_status = db_results.get('neo4j', {}).get('status', 'unknown')
        redis_status = db_results.get('redis', {}).get('status', 'unknown')

        print(f"{Fore.WHITE}MongoDB: {Fore.GREEN if mongodb_status == 'connected' else Fore.RED}{mongodb_status}")
        print(f"{Fore.WHITE}Neo4j: {Fore.GREEN if neo4j_status == 'connected' else Fore.RED}{neo4j_status}")
        print(f"{Fore.WHITE}Redis: {Fore.GREEN if redis_status == 'connected' else Fore.RED}{redis_status}")

    except Exception as e:
        print(f"\n{Fore.RED}ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()