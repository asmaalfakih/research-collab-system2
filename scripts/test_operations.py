
import sys
import os
from pathlib import Path
from colorama import init, Fore, Style

sys.path.append(str(Path(__file__).parent.parent))

init(autoreset=True)

def test_delete_researcher():
    from app.database.mongodb import mongodb
    from app.services.researcher_service import ResearcherService

    print(f"\n{Fore.YELLOW}Testing Researcher Deletion")
    print(f"{Fore.CYAN}{'-' * 50}")

    researcher = mongodb.db.researchers.find_one({
        'profile_status': 'approved',
        'role': 'researcher'
    })

    if not researcher:
        print(f"{Fore.RED}No test researcher found")
        return

    researcher_id = str(researcher['_id'])
    print(f"{Fore.WHITE}Test researcher:")
    print(f"  Name: {researcher['name']}")
    print(f"  Email: {researcher['email']}")
    print(f"  ID: {researcher_id}")

    confirm = input(f"\n{Fore.YELLOW}Test delete this researcher? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print(f"{Fore.YELLOW}Cancelled")
        return

    admin = mongodb.db.researchers.find_one({'role': 'admin'})
    if not admin:
        admin_id = 'system'
    else:
        admin_id = str(admin['_id'])

    print(f"\n{Fore.YELLOW}Starting deletion test...")
    success, message = ResearcherService.delete_researcher_complete(researcher_id, admin_id)

    if success:
        print(f"{Fore.GREEN}SUCCESS: {message}")
    else:
        print(f"{Fore.RED}FAILED: {message}")

def test_create_project():
    from app.database.mongodb import mongodb
    from app.services.project_service import ProjectService

    print(f"\n{Fore.YELLOW}Testing Project Creation")
    print(f"{Fore.CYAN}{'-' * 50}")

    researcher = mongodb.db.researchers.find_one({
        'profile_status': 'approved'
    })

    if not researcher:
        print(f"{Fore.RED}No researcher found")
        return

    researcher_id = str(researcher['_id'])
    print(f"{Fore.WHITE}Creating project for:")
    print(f"  Researcher: {researcher['name']}")
    print(f"  ID: {researcher_id}")

    project_data = {
        'title': f"Test Project - {os.urandom(4).hex()}",
        'description': 'This is a test project for debugging',
        'research_area': 'Computer Science',
        'status': 'active'
    }

    print(f"\n{Fore.YELLOW}Project data:")
    for key, value in project_data.items():
        print(f"  {key}: {value}")

    confirm = input(f"\n{Fore.YELLOW}Create this project? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print(f"{Fore.YELLOW}Cancelled")
        return

    print(f"\n{Fore.YELLOW}Creating project...")
    success, project_id, message = ProjectService.create_project(researcher_id, project_data)

    if success:
        print(f"{Fore.GREEN}SUCCESS: {message}")
        print(f"{Fore.CYAN}Project ID: {project_id}")

        project = mongodb.db.projects.find_one({'_id': ObjectId(project_id)})
        if project:
            print(f"\n{Fore.GREEN}Project verified in MongoDB:")
            print(f"  Title: {project.get('title')}")
            print(f"  Creator: {project.get('creator_name')}")
            print(f"  Status: {project.get('status')}")
    else:
        print(f"{Fore.RED}FAILED: {message}")

def check_database_counts():
    from app.database.mongodb import mongodb
    from app.database.neo4j import neo4j
    from app.database.redis import redis_manager

    print(f"\n{Fore.YELLOW}Database Counts")
    print(f"{Fore.CYAN}{'-' * 50}")

    print(f"\n{Fore.GREEN}MongoDB:")
    print(f"{Fore.WHITE}  Researchers: {mongodb.db.researchers.count_documents({})}")
    print(f"{Fore.WHITE}  Projects: {mongodb.db.projects.count_documents({})}")
    print(f"{Fore.WHITE}  Publications: {mongodb.db.publications.count_documents({})}")

    if neo4j.driver:
        with neo4j.driver.session() as session:
            result = session.run("MATCH (r:Researcher) RETURN count(r) as count")
            record = result.single()
            print(f"\n{Fore.GREEN}Neo4j:")
            print(f"{Fore.WHITE}  Researcher nodes: {record['count'] if record else 0}")

            result = session.run("MATCH ()-[r]-() RETURN count(r) as count")
            record = result.single()
            print(f"{Fore.WHITE}  Relationships: {record['count'] if record else 0}")

    if redis_manager.is_connected():
        keys = redis_manager.client.keys("*")
        print(f"\n{Fore.GREEN}Redis:")
        print(f"{Fore.WHITE}  Total keys: {len(keys)}")

if __name__ == "__main__":
    print(f"{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.YELLOW}OPERATIONS TESTING TOOL")
    print(f"{Fore.CYAN}{'=' * 60}")

    print(f"\n{Fore.GREEN}Available tests:")
    print(f"{Fore.WHITE}[1] Test researcher deletion")
    print(f"{Fore.WHITE}[2] Test project creation")
    print(f"{Fore.WHITE}[3] Check database counts")
    print(f"{Fore.WHITE}[0] Exit")

    choice = input(f"\n{Fore.YELLOW}Select test: ").strip()

    if choice == '1':
        test_delete_researcher()
    elif choice == '2':
        test_create_project()
    elif choice == '3':
        check_database_counts()
    elif choice == '0':
        print(f"{Fore.YELLOW}Exiting...")
    else:
        print(f"{Fore.RED}Invalid choice")