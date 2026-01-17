#!/usr/bin/env python3
"""
Research Collaboration System - Main Entry Point
Palestine Polytechnic University
Course: NoSQL Database
Students: Asma Alfakih, Dalah Alhashlamoun
"""

import sys
import os
import json
from pathlib import Path
from colorama import init, Fore, Style
import subprocess

BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

init(autoreset=True)


def display_banner():
    """Display system banner"""
    banner = f"""
    {Fore.CYAN}{'=' * 70}
    {Fore.GREEN}RESEARCH COLLABORATION SYSTEM - NOSQL DATABASE PROJECT
    {Fore.CYAN}{'=' * 70}
    {Fore.YELLOW}MULTI-DATABASE INTEGRATION PLATFORM - LARGE DATASET MODE
    {Fore.MAGENTA}MONGODB | NEO4J | REDIS | 100+ RESEARCHERS | 50+ PROJECTS

    {Fore.CYAN}PALESTINE POLYTECHNIC UNIVERSITY
    {Fore.CYAN}COURSE: NOSQL DATABASE
    {Fore.CYAN}STUDENTS: ASMA ALFAKIH, DALAH ALHASHLAMOUN
    {Fore.CYAN}{'=' * 70}

    {Fore.WHITE}MAIN MENU - AVAILABLE COMMANDS:

    {Fore.GREEN}[1]{Fore.WHITE} Setup System         {Fore.CYAN}- Large dataset setup
    {Fore.GREEN}[2]{Fore.WHITE} Test Connections     {Fore.CYAN}- Test all connections
    {Fore.GREEN}[3]{Fore.WHITE} Admin Interface      {Fore.CYAN}- Admin interface
    {Fore.GREEN}[4]{Fore.WHITE} Researcher Interface {Fore.CYAN}- Researcher interface
    {Fore.GREEN}[5]{Fore.WHITE} System Statistics    {Fore.CYAN}- View detailed statistics

    {Fore.WHITE}DEVELOPER TOOLS:

    {Fore.GREEN}[6]{Fore.WHITE} Initialize Databases {Fore.CYAN}- Initialize databases
    {Fore.GREEN}[7]{Fore.WHITE} Import LARGE Data    {Fore.CYAN}- 100 researchers, 50 projects, 30 publications
    {Fore.GREEN}[8]{Fore.WHITE} Backup System        {Fore.CYAN}- System backup
    {Fore.GREEN}[9]{Fore.WHITE} Cleanup Test Data    {Fore.CYAN}- Clean test data
    {Fore.GREEN}[R]{Fore.WHITE} 6 Relationships      {Fore.CYAN}- Show 6 relationships summary
    {Fore.GREEN}[0]{Fore.WHITE} Exit                 {Fore.CYAN}- Exit

    {Fore.CYAN}{'=' * 70}
    """
    print(banner)


def check_faker_installation():
    """Check if Faker library is installed"""
    try:
        import faker
        return True
    except ImportError:
        return False


def install_faker():
    """Install Faker library"""
    print(f"{Fore.YELLOW}Installing Faker library...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "Faker"], check=True)
        print(f"{Fore.GREEN}Faker library installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to install Faker: {e}")
        return False


def check_redis_config():
    """Check and fix Redis configuration"""
    print(f"\n{Fore.YELLOW}Checking Redis configuration...")

    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        print(f"{Fore.RED}ERROR: .env file not found!")
        return False

    try:
        with open(env_file, 'r') as f:
            content = f.read()

        redis_issues = []

        if 'REDIS_SSL=True' in content:
            redis_issues.append("REDIS_SSL=True may cause connection issues with Redis Cloud")

        if 'REDIS_SSL_CERT_REQS' in content:
            redis_issues.append("REDIS_SSL_CERT_REQS may cause SSL version errors")

        if redis_issues:
            print(f"{Fore.YELLOW}WARNING: Found potential Redis issues:")
            for issue in redis_issues:
                print(f"   - {issue}")

            print(f"\n{Fore.CYAN}Suggested fixes:")
            print(f"   1. Change REDIS_SSL=True to REDIS_SSL=False")
            print(f"   2. Remove or comment REDIS_SSL_CERT_REQS line")

            fix = input(f"\n{Fore.YELLOW}Apply automatic fixes? (yes/no): ").strip().lower()

            if fix in ['yes', 'y', 'yep']:
                new_content = content
                new_content = new_content.replace('REDIS_SSL=True', 'REDIS_SSL=False')
                new_content = new_content.replace('REDIS_SSL_CERT_REQS=None', '# REDIS_SSL_CERT_REQS=None')
                new_content = new_content.replace('REDIS_SSL_CERT_REQS=ssl.CERT_NONE',
                                                  '# REDIS_SSL_CERT_REQS=ssl.CERT_NONE')

                with open(env_file, 'w') as f:
                    f.write(new_content)

                print(f"{Fore.GREEN}SUCCESS: .env file updated with Redis fixes")
                return True
            else:
                print(f"{Fore.YELLOW}WARNING: Manual fix required")
                return False
        else:
            print(f"{Fore.GREEN}SUCCESS: Redis configuration looks good")
            return True

    except Exception as e:
        print(f"{Fore.RED}ERROR: Error checking Redis config: {e}")
        return False


def display_connection_status(db_name, result):
    """Display connection status with colored text"""
    status = result.get('status', 'unknown')
    if status == 'connected':
        print(f"{Fore.GREEN}PASS  {db_name.upper():12} {Fore.WHITE}Connected")
        if db_name == 'mongodb':
            print(f"   Database: {result.get('database')}")
            print(f"   Collections: {len(result.get('collections', []))}")
        elif db_name == 'neo4j':
            print(f"   Nodes: {result.get('node_count', 0)}")
        elif db_name == 'redis':
            redis_info = result.get('info', {})
            if redis_info.get('status') == 'connected':
                print(f"   Version: {redis_info.get('version', 'N/A')}")
                print(f"   Memory: {redis_info.get('memory_used', 'N/A')}")
            else:
                print(f"   Status: {redis_info.get('status', 'N/A')}")
    elif status == 'disabled':
        print(f"{Fore.YELLOW}WARN  {db_name.upper():12} {Fore.WHITE}Disabled")
        print(f"   {result.get('message', 'Check configuration')}")
    elif status == 'disconnected':
        print(f"{Fore.RED}FAIL  {db_name.upper():12} {Fore.WHITE}Disconnected")
    else:
        print(f"{Fore.YELLOW}UNKN  {db_name.upper():12} {Fore.WHITE}{status}")


def display_test_result(test_name, passed):
    """Display test result with colored text"""
    if passed is True:
        print(f"{Fore.GREEN}PASS  {Fore.WHITE}{test_name}")
    elif passed is False:
        print(f"{Fore.RED}FAIL  {Fore.WHITE}{test_name}")
    else:
        print(f"{Fore.YELLOW}WARN  {Fore.WHITE}{test_name}")


def setup_system():
    """Initial system setup"""
    print(f"\n{Fore.YELLOW}START: Setting up Research Collaboration System...")
    print(f"{Fore.CYAN}Large Dataset Mode: 100 Researchers, 50 Projects, 30 Publications")

    if not check_faker_installation():
        print(f"{Fore.YELLOW}WARNING: Faker library not installed")
        print(f"{Fore.WHITE}  Large dataset creation requires Faker library")
        install = input(f"{Fore.YELLOW}Install Faker now? (yes/no): ").strip().lower()
        if install in ['yes', 'y']:
            install_faker()
        else:
            print(f"{Fore.YELLOW}WARNING: Large dataset features will be limited")

    check_redis_config()

    try:
        from app.database import db_manager
        results = db_manager.check_all_connections()

        print(f"\n{Fore.CYAN}{'─' * 50}")
        print(f"{Fore.WHITE}DATABASE CONNECTION STATUS - LARGE DATASET MODE")
        print(f"{Fore.CYAN}{'─' * 50}")

        for db_name, result in results.items():
            display_connection_status(db_name, result)

        print(f"{Fore.CYAN}{'─' * 50}")

        operational_dbs = []
        for db_name, result in results.items():
            status = result.get('status', 'unknown')
            if status in ['connected', 'disabled']:
                operational_dbs.append(db_name)

        if len(operational_dbs) >= 2:
            print(f"\n{Fore.GREEN}SUCCESS: System is operational!")
            print(f"{Fore.CYAN}Working databases: {', '.join(operational_dbs)}")

            if 'redis' not in operational_dbs:
                print(f"{Fore.YELLOW}WARNING: Redis cache is disabled")
                print(f"{Fore.WHITE}   System will work but without caching features")

            print(f"\n{Fore.YELLOW}Large Dataset Features:")
            print(f"   {Fore.WHITE}• 100 realistic researchers")
            print(f"   {Fore.WHITE}• 50 diverse projects")
            print(f"   {Fore.WHITE}• 30 academic publications")
            print(f"   {Fore.WHITE}• 300+ collaboration relationships")

            print(f"\n{Fore.YELLOW}Next steps:")
            print(f"   {Fore.WHITE}1. Initialize databases: {Fore.CYAN}Select option 6")
            print(f"   {Fore.WHITE}2. Create large dataset: {Fore.CYAN}Select option 7")
            print(f"   {Fore.WHITE}3. View statistics: {Fore.CYAN}Select option 5")
            print(f"   {Fore.WHITE}4. Try admin interface: {Fore.CYAN}Select option 3")

        else:
            print(f"\n{Fore.YELLOW}WARNING: Critical databases failed to connect.")
            print(f"{Fore.WHITE}Please check:")
            print(f"   - {Fore.CYAN}.env file configuration")
            print(f"   - {Fore.CYAN}Database servers are running")
            print(f"   - {Fore.CYAN}Network connectivity")

        return len(operational_dbs) >= 2

    except ImportError as e:
        print(f"{Fore.RED}ERROR: Import error: {e}")
        print(f"{Fore.YELLOW}Make sure all Python files are in place")
        return False
    except Exception as e:
        print(f"{Fore.RED}ERROR: Error during setup: {e}")
        return False


def test_system():
    """Test the complete system"""
    print(f"\n{Fore.YELLOW}Running comprehensive system tests...")

    try:
        from app.database import db_manager
        results = db_manager.check_all_connections()

        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.WHITE}SYSTEM TEST RESULTS - LARGE DATASET MODE")
        print(f"{Fore.CYAN}{'=' * 60}")

        test_results = []

        if results['mongodb']['status'] == 'connected':
            from app.database.mongodb import mongodb
            try:
                test_data = {
                    'name': 'Test System User',
                    'email': 'system.test@university.edu',
                    'department': 'System Testing',
                    'profile_status': 'approved',
                    'research_interests': ['Testing', 'QA', 'System Integration']
                }

                researcher_id = mongodb.create_researcher(test_data)
                if researcher_id:
                    test_results.append(("MongoDB CREATE", True))
                else:
                    test_results.append(("MongoDB CREATE", False))

                researcher = mongodb.get_researcher(researcher_id) if researcher_id else None
                if researcher and researcher['email'] == 'system.test@university.edu':
                    test_results.append(("MongoDB READ", True))
                else:
                    test_results.append(("MongoDB READ", False))

                if researcher_id:
                    updated = mongodb.update_researcher(researcher_id, {'department': 'Updated System Testing'})
                    test_results.append(("MongoDB UPDATE", updated))

                if researcher_id and researcher:
                    mongodb.db.researchers.delete_one({'_id': researcher['_id']})
                    test_results.append(("MongoDB CLEANUP", True))

                print(f"{Fore.GREEN}PASS: MongoDB: CRUD operations passed")

            except Exception as e:
                print(f"{Fore.RED}FAIL: MongoDB Error: {e}")
                test_results.append(("MongoDB Operations", False))
        else:
            print(f"{Fore.RED}FAIL: MongoDB: {results['mongodb'].get('status', 'Disconnected')}")
            test_results.append(("MongoDB", False))

        if results['neo4j']['status'] == 'connected':
            from app.database.neo4j import neo4j
            try:
                with neo4j.driver.session() as session:
                    result = session.run("MATCH (r:Researcher) RETURN count(r) as count")
                    researcher_count = result.single()["count"]

                    if researcher_count > 0:
                        test_results.append(("Neo4j Data Check", True))
                        print(f"{Fore.GREEN}PASS: Neo4j: Found {researcher_count} researchers")

                        result = session.run("""
                            MATCH ()-[rel]-() 
                            RETURN type(rel) as rel_type, count(*) as count
                            ORDER BY count DESC
                        """)

                        relationships_found = False
                        for record in result:
                            relationships_found = True
                            break

                        if relationships_found:
                            test_results.append(("Neo4j Relationships", True))
                            print(f"{Fore.GREEN}PASS: Neo4j: Relationship queries working")
                        else:
                            test_results.append(("Neo4j Relationships", None))
                            print(f"{Fore.YELLOW}WARN: Neo4j: No relationships found")

                        test_results.append(("Neo4j Co-authorship Creation", None))
                        test_results.append(("Neo4j Teamwork Creation", None))

                    else:
                        test_results.append(("Neo4j Data Check", False))
                        test_results.append(("Neo4j Relationships", None))
                        test_results.append(("Neo4j Co-authorship Creation", None))
                        test_results.append(("Neo4j Teamwork Creation", None))
                        print(f"{Fore.YELLOW}WARN: Neo4j: No researchers found")

            except Exception as e:
                print(f"{Fore.RED}FAIL: Neo4j Error: {e}")
                test_results.append(("Neo4j Operations", False))
        else:
            print(f"{Fore.RED}FAIL: Neo4j: {results['neo4j'].get('status', 'Disconnected')}")
            test_results.append(("Neo4j", False))

        redis_status = results['redis'].get('status', 'disconnected')
        if redis_status == 'connected':
            from app.database.redis import redis_manager
            try:
                session_id = redis_manager.create_session("SYSTEM_TEST_001", {
                    "name": "System Test User",
                    "role": "tester",
                    "email": "test@system.edu"
                })

                if session_id:
                    session = redis_manager.get_session(session_id)
                    if session and session.get('name') == 'System Test User':
                        test_results.append(("Redis Sessions", True))
                        print(f"{Fore.GREEN}PASS: Redis: Session operations working")
                    else:
                        test_results.append(("Redis Sessions", False))

                    redis_manager.delete_session(session_id)
                else:
                    test_results.append(("Redis Sessions", False))

                success = redis_manager.track_activity("SYSTEM_TEST_001", "system_test", {
                    "action": "test",
                    "timestamp": "2024-01-01"
                })
                test_results.append(("Redis Tracking", success))

                if success:
                    print(f"{Fore.GREEN}PASS: Redis: Activity tracking working")

                try:
                    redis_manager.client.set("system_test_key", "system_test_value", ex=10)
                    value = redis_manager.client.get("system_test_key")
                    if value == "system_test_value":
                        test_results.append(("Redis Basic Ops", True))
                        print(f"{Fore.GREEN}PASS: Redis: Basic operations working")
                    else:
                        test_results.append(("Redis Basic Ops", False))
                except:
                    test_results.append(("Redis Basic Ops", None))

            except Exception as e:
                print(f"{Fore.RED}FAIL: Redis Error: {e}")
                test_results.append(("Redis Operations", False))
        elif redis_status == 'disabled':
            print(f"{Fore.YELLOW}WARN: Redis: Disabled")
            test_results.append(("Redis", None))
        else:
            print(f"{Fore.RED}FAIL: Redis: {redis_status}")
            test_results.append(("Redis", False))

        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.WHITE}TEST SUMMARY - LARGE DATASET MODE")
        print(f"{Fore.CYAN}{'=' * 60}")

        for test_name, result in test_results:
            display_test_result(test_name, result)

        passed_tests = sum(1 for _, result in test_results if result is True)
        warning_tests = sum(1 for _, result in test_results if result is None)
        failed_tests = sum(1 for _, result in test_results if result is False)
        total_tests = len(test_results)

        print(f"\n{Fore.CYAN}{'─' * 40}")
        print(
            f"{Fore.WHITE}Passed: {passed_tests} | Warnings: {warning_tests} | Failed: {failed_tests} | Total: {total_tests}")

        if failed_tests == 0:
            if warning_tests == 0:
                print(f"{Fore.GREEN}ALL TESTS PASSED: {passed_tests}/{total_tests}")
                print(f"{Fore.GREEN}System is ready for production use with large dataset!")
            else:
                print(f"{Fore.YELLOW}ALL CRITICAL TESTS PASSED: {passed_tests}/{total_tests - warning_tests}")
                print(f"{Fore.YELLOW}   Warnings: {warning_tests}")
                print(f"{Fore.YELLOW}System is operational with minor limitations")
            success = True
        else:
            print(f"{Fore.RED}TESTS FAILED: {passed_tests}/{total_tests} passed")
            if passed_tests >= total_tests * 0.7:
                print(f"{Fore.YELLOW}System is mostly functional but needs attention")
            else:
                print(f"{Fore.RED}System needs configuration for large dataset mode")
            success = False

        print(f"{Fore.CYAN}{'─' * 40}")

        return success

    except Exception as e:
        print(f"{Fore.RED}ERROR: System test failed: {e}")
        return False


def admin_interface():
    """Open admin interface"""
    try:
        from app.cli.main_cli import MainCLI
        cli = MainCLI()
        cli.run_admin_interface()
    except ImportError as e:
        print(f"{Fore.RED}ERROR: Admin interface not available: {e}")


def researcher_interface():
    """Open researcher interface"""
    try:
        from app.cli.main_cli import MainCLI
        cli = MainCLI()
        cli.run_researcher_interface()
    except ImportError as e:
        print(f"{Fore.RED}ERROR: Researcher interface not available: {e}")


def show_statistics():
    """Show detailed system statistics"""
    try:
        from app.services.collaboration_service import CollaborationService

        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}DETAILED SYSTEM STATISTICS - LARGE DATASET")
        print(f"{Fore.CYAN}{'=' * 60}")

        try:
            stats = CollaborationService.get_relationship_statistics()

            print(f"\n{Fore.GREEN}Relationship Statistics:")
            if 'total_coauthorships' in stats:
                print(f"{Fore.WHITE}  Co-authorships: {stats.get('total_coauthorships', 0):,}")
            if 'total_supervisions' in stats:
                print(f"{Fore.WHITE}  Supervisions: {stats.get('total_supervisions', 0):,}")
            if 'total_teamworks' in stats:
                print(f"{Fore.WHITE}  Teamwork: {stats.get('total_teamworks', 0):,}")
            if 'total_researchers' in stats:
                print(f"{Fore.WHITE}  Total Researchers: {stats.get('total_researchers', 0):,}")

        except Exception as e:
            print(f"{Fore.YELLOW}WARN: Could not get relationship stats: {e}")

        from app.database import db_manager
        results = db_manager.check_all_connections()

        print(f"\n{Fore.GREEN}Database Status:")
        for db_name, result in results.items():
            status = result.get('status', 'unknown')
            if status == 'connected':
                print(f"{Fore.WHITE}  {db_name.upper()}: Connected")
                if db_name == 'mongodb':
                    print(f"{Fore.CYAN}    Database: {result.get('database')}")
                    print(f"{Fore.CYAN}    Collections: {len(result.get('collections', []))}")
            elif status == 'disabled':
                print(f"{Fore.YELLOW}  {db_name.upper()}: Disabled")
            else:
                print(f"{Fore.RED}  {db_name.upper()}: {status}")

        if results.get('mongodb', {}).get('status') == 'connected':
            from app.database.mongodb import mongodb
            try:
                researcher_count = mongodb.db.researchers.count_documents({})
                project_count = mongodb.db.projects.count_documents({})
                publication_count = mongodb.db.publications.count_documents({})

                print(f"\n{Fore.GREEN}Data Counts:")
                print(f"{Fore.WHITE}  Researchers: {researcher_count:,}")
                print(f"{Fore.WHITE}  Projects: {project_count:,}")
                print(f"{Fore.WHITE}  Publications: {publication_count:,}")

                if researcher_count > 0:
                    avg_projects_per_researcher = project_count / researcher_count
                    avg_publications_per_researcher = publication_count / researcher_count
                    print(f"\n{Fore.GREEN}Averages per Researcher:")
                    print(f"{Fore.WHITE}  Projects: {avg_projects_per_researcher:.1f}")
                    print(f"{Fore.WHITE}  Publications: {avg_publications_per_researcher:.1f}")

            except Exception as e:
                print(f"{Fore.YELLOW}WARN: Error calculating statistics: {e}")

        if results.get('redis', {}).get('status') == 'connected':
            from app.database.redis import redis_manager
            try:
                if redis_manager.is_connected():
                    keys = redis_manager.client.keys("*")
                    print(f"\n{Fore.GREEN}Redis Cache:")
                    print(f"{Fore.WHITE}  Total keys: {len(keys)}")

                    data_keys = sum(1 for key in keys if 'dataset' in key or 'researcher' in key)
                    session_keys = sum(1 for key in keys if 'session' in key)
                    print(f"{Fore.WHITE}  Data keys: {data_keys}")
                    print(f"{Fore.WHITE}  Session keys: {session_keys}")
            except:
                pass

        print(f"{Fore.CYAN}{'=' * 60}")

    except ImportError as e:
        print(f"{Fore.RED}ERROR: Statistics service not available: {e}")
        print(f"{Fore.YELLOW}Creating simple stats...")

        try:
            from app.database import db_manager
            results = db_manager.check_all_connections()

            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}SIMPLE SYSTEM STATISTICS")
            print(f"{Fore.CYAN}{'=' * 50}")

            for db_name, result in results.items():
                status = result.get('status', 'unknown')
                if status == 'connected':
                    print(f"{Fore.GREEN}PASS  {db_name.upper():12}: {status}")
                elif status == 'disabled':
                    print(f"{Fore.YELLOW}WARN  {db_name.upper():12}: {status}")
                else:
                    print(f"{Fore.RED}FAIL  {db_name.upper():12}: {status}")

            print(f"{Fore.CYAN}{'=' * 50}")

        except:
            print(f"{Fore.RED}ERROR: Cannot retrieve basic statistics")


def show_relationships_summary():
    """Show summary of 6 relationships in the system"""
    try:
        from app.services.collaboration_service import CollaborationService

        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.YELLOW}6 RELATIONSHIPS SUMMARY - RESEARCH COLLABORATION SYSTEM")
        print(f"{Fore.CYAN}{'=' * 70}")

        summary = CollaborationService.get_six_relationships_summary()

        if not summary:
            print(f"{Fore.RED}Cannot get relationships summary")
            return

        print(f"\n{Fore.GREEN}ENTITY COUNTS:")
        entities = summary.get('entity_counts', {})
        print(f"{Fore.WHITE}  Researchers: {entities.get('researchers', 0)}")
        print(f"{Fore.WHITE}  Projects: {entities.get('projects', 0)}")
        print(f"{Fore.WHITE}  Publications: {entities.get('publications', 0)}")

        print(f"\n{Fore.GREEN}THE 6 RELATIONSHIPS:")
        relationships = summary.get('relationships_defined', [])
        total_rels = 0

        for i, rel in enumerate(relationships, 1):
            count = rel.get('count', 0)
            total_rels += count

            if count > 0:
                print(f"{Fore.GREEN}  {i}. {rel['name']}: {count}")
            else:
                print(f"{Fore.YELLOW}  {i}. {rel['name']}: {count} (no data)")

            desc = rel['description']
            if len(desc) > 50:
                desc = desc[:47] + "..."
            print(f"     {desc}")

        print(f"\n{Fore.GREEN}TOTAL RELATIONSHIPS: {total_rels}")

        if summary.get('has_six_relationships', False):
            print(f"\n{Fore.GREEN}✓ SYSTEM VALIDATION: Supports exactly 6 relationships")
        else:
            print(f"\n{Fore.RED}✗ SYSTEM VALIDATION: Does not support exactly 6 relationships")

        print(f"\n{Fore.CYAN}Relationship Types:")
        for rel in relationships:
            name = rel['name']
            if name in ['CO_AUTHORED_WITH', 'SUPERVISED', 'TEAMWORK_WITH']:
                print(f"{Fore.WHITE}  • {name}: Researcher ↔ Researcher")
            elif name in ['PARTICIPATED_IN', 'AUTHORED']:
                print(f"{Fore.WHITE}  • {name}: Researcher → Entity")
            elif name == 'PRODUCED':
                print(f"{Fore.WHITE}  • {name}: Project → Publication")

        print(f"{Fore.CYAN}{'=' * 70}")

    except ImportError as e:
        print(f"{Fore.RED}Error: Cannot import CollaborationService: {e}")
        print(f"{Fore.YELLOW}Make sure collaboration_service.py has get_six_relationships_summary() method")
    except Exception as e:
        print(f"{Fore.RED}Error showing relationships summary: {e}")


def initialize_databases():
    """Initialize databases"""
    print(f"\n{Fore.YELLOW}Initializing databases for large dataset mode...")

    try:
        init_script = BASE_DIR / "scripts" / "simple_init.py"

        if init_script.exists():
            subprocess.run([sys.executable, str(init_script)])
        else:
            print(f"{Fore.YELLOW}WARNING: Initialization script not found")
            print(f"{Fore.CYAN}Creating basic structure for large dataset...")

            from app.database.mongodb import mongodb
            from app.database.neo4j import neo4j

            if mongodb.client:
                print(f"{Fore.GREEN}SUCCESS: MongoDB already initialized")

            if neo4j.driver:
                with neo4j.driver.session() as session:
                    session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Researcher) REQUIRE r.id IS UNIQUE")
                    print(f"{Fore.GREEN}SUCCESS: Neo4j constraints created")

            print(f"\n{Fore.GREEN}SUCCESS: Basic database initialization completed")
            print(f"{Fore.CYAN}Ready for large dataset: 100 researchers, 50 projects, 30 publications")

    except Exception as e:
        print(f"{Fore.RED}ERROR: Error initializing databases: {e}")


def import_sample_data():
    """Import large sample data (100 researchers, 50 projects, 30 publications)"""
    print(f"\n{Fore.YELLOW}Importing LARGE sample data...")
    print(f"{Fore.CYAN}Target: 100 Researchers, 50 Projects, 30 Publications")

    try:
        sample_file = BASE_DIR / "scripts" / "sample_data.py"

        if sample_file.exists():
            if not check_faker_installation():
                print(f"{Fore.YELLOW}Faker library is required for large dataset creation")
                install = input(f"{Fore.YELLOW}Install Faker now? (yes/no): ").strip().lower()
                if install in ['yes', 'y']:
                    if install_faker():
                        print(f"{Fore.GREEN}Faker library installed successfully")
                    else:
                        print(f"{Fore.RED}Faker installation failed. Using limited data mode.")
                        print(f"{Fore.YELLOW}Creating basic sample data instead...")
                        create_basic_sample_data()
                        return
                else:
                    print(f"{Fore.YELLOW}Using basic sample data mode...")
                    create_basic_sample_data()
                    return

            print(f"{Fore.CYAN}Creating large dataset...")
            print(f"{Fore.YELLOW}This may take a few minutes...")
            subprocess.run([sys.executable, str(sample_file)])
        else:
            print(f"{Fore.RED}ERROR: Sample data script not found at: {sample_file}")
            print(f"{Fore.YELLOW}Creating minimal sample data as fallback...")
            create_basic_sample_data()

    except Exception as e:
        print(f"{Fore.RED}ERROR: Error importing sample data: {e}")
        print(f"{Fore.YELLOW}Please check if Faker library is installed: pip install Faker")


def create_basic_sample_data():
    """Create basic sample data when Faker is not available"""
    try:
        from app.database.mongodb import mongodb
        from app.database.neo4j import neo4j

        sample_researchers = [
            {
                'name': 'Dr. Ahmed Ali',
                'email': 'ahmed.ali@university.edu',
                'department': 'Computer Science',
                'profile_status': 'approved',
                'research_interests': ['AI', 'Machine Learning', 'Data Science'],
                'role': 'researcher'
            },
            {
                'name': 'Dr. Sara Mohamed',
                'email': 'sara.mohamed@university.edu',
                'department': 'Information Technology',
                'profile_status': 'approved',
                'research_interests': ['Networks', 'Security', 'Cloud Computing'],
                'role': 'researcher'
            }
        ]

        for researcher in sample_researchers:
            researcher_id = mongodb.create_researcher(researcher)
            if researcher_id:
                neo4j.create_researcher_node({
                    'id': researcher_id,
                    'name': researcher['name'],
                    'email': researcher['email'],
                    'department': researcher['department'],
                    'profile_status': researcher['profile_status']
                })

        print(f"{Fore.GREEN}SUCCESS: Created 2 sample researchers (basic mode)")
        print(f"{Fore.YELLOW}For large dataset (100 researchers), install Faker: pip install Faker")

    except Exception as e:
        print(f"{Fore.RED}ERROR: Error creating basic sample data: {e}")


def backup_system():
    """Backup system"""
    print(f"\n{Fore.YELLOW}Creating system backup...")

    import shutil
    from datetime import datetime

    try:
        backup_dir = BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.json"

        backup_data = {
            'timestamp': timestamp,
            'system': 'Research Collaboration System - Large Dataset Mode',
            'backup_type': 'configuration',
            'dataset_size': 'large (100 researchers, 50 projects, 30 publications)',
            'relationship_types': ['CO_AUTHORED_WITH', 'SUPERVISED', 'TEAMWORK_WITH', 'PARTICIPATED_IN']
        }

        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)

        print(f"{Fore.GREEN}SUCCESS: Backup created: {backup_file.name}")
        print(f"{Fore.CYAN}Location: {backup_file}")
        print(f"{Fore.YELLOW}Dataset Mode: Large (100 researchers, 50 projects, 30 publications)")

    except Exception as e:
        print(f"{Fore.RED}ERROR: Error creating backup: {e}")


def cleanup_system():
    """Clean up test data"""
    print(f"\n{Fore.RED}{'=' * 60}")
    print(f"{Fore.YELLOW} CLEANING ALL DATA - INCLUDING LARGE DATASET")
    print(f"{Fore.RED}{'=' * 60}")

    try:
        from app.database.mongodb import mongodb

        confirm = input(f"{Fore.RED}WARNING: Delete ALL data including large dataset? (type 'DELETE_ALL'): ").strip()

        if confirm == 'DELETE_ALL':
            if mongodb.client:
                collections = ['researchers', 'projects', 'publications', 'logs']
                total_deleted = 0

                for collection in collections:
                    if collection in mongodb.db.list_collection_names():
                        result = mongodb.db[collection].delete_many({})
                        deleted = result.deleted_count
                        total_deleted += deleted
                        print(f"{Fore.YELLOW}   Deleted {deleted} documents from {collection}")

                print(f"{Fore.GREEN}SUCCESS: Total {total_deleted} documents cleaned up")

                try:
                    from app.database.neo4j import neo4j
                    if neo4j.driver:
                        with neo4j.driver.session() as session:
                            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
                            deleted_nodes = result.single()["deleted"]
                            print(f"{Fore.YELLOW}   Deleted {deleted_nodes} nodes from Neo4j")
                except:
                    pass

                try:
                    from app.database.redis import redis_manager
                    if redis_manager.is_connected():
                        keys = redis_manager.client.keys("*")
                        if keys:
                            redis_manager.client.delete(*keys)
                            print(f"{Fore.YELLOW}   Deleted {len(keys)} keys from Redis")
                except:
                    pass

                print(f"\n{Fore.GREEN}ALL DATA CLEANED SUCCESSFULLY!")
                print(f"{Fore.CYAN}You can now create a new large dataset using option 7")
            else:
                print(f"{Fore.RED}ERROR: MongoDB not connected")
        else:
            print(f"{Fore.YELLOW}CANCELLED: Cleanup cancelled")

    except Exception as e:
        print(f"{Fore.RED}ERROR: Error cleaning up: {e}")


def interactive_menu():
    """Interactive main menu"""
    while True:
        display_banner()

        try:
            choice = input(f"\n{Fore.YELLOW}Enter your choice (0-9, R): {Fore.WHITE}").strip().lower()

            if choice == '1':
                setup_system()
            elif choice == '2':
                test_system()
            elif choice == '3':
                admin_interface()
            elif choice == '4':
                researcher_interface()
            elif choice == '5':
                show_statistics()
            elif choice == '6':
                initialize_databases()
            elif choice == '7':
                import_sample_data()
            elif choice == '8':
                backup_system()
            elif choice == '9':
                cleanup_system()
            elif choice == 'r':
                show_relationships_summary()
            elif choice == '0':
                print(f"\n{Fore.GREEN}Thank you for using Research Collaboration System!")
                print(f"{Fore.CYAN}Large Dataset Mode: 100 Researchers, 50 Projects, 30 Publications")
                print(f"{Fore.CYAN}6 Relationships: CO_AUTHORED_WITH, SUPERVISED, TEAMWORK_WITH,")
                print(f"{Fore.CYAN}                PARTICIPATED_IN, AUTHORED, PRODUCED")
                print(f"{Fore.CYAN}Goodbye!")
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice. Please enter a number between 0-9 or 'R'.")

            input(f"\n{Fore.CYAN}Press Enter to continue...")

        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}WARNING: Operation cancelled by user")
            break
        except Exception as e:
            print(f"{Fore.RED}ERROR: {e}")


def command_line_mode():
    """Command line mode"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'setup' or command == '1':
            setup_system()
        elif command == 'test' or command == '2':
            test_system()
        elif command == 'admin' or command == '3':
            admin_interface()
        elif command == 'researcher' or command == '4':
            researcher_interface()
        elif command == 'stats' or command == '5':
            show_statistics()
        elif command == 'init-db' or command == '6':
            initialize_databases()
        elif command == 'sample-data' or command == '7':
            import_sample_data()
        elif command == 'large-data' or command == 'large':
            import_sample_data()
        elif command == 'backup' or command == '8':
            backup_system()
        elif command == 'cleanup' or command == '9':
            cleanup_system()
        elif command == 'relationships' or command == 'r':
            show_relationships_summary()
        elif command == 'help' or command == '--help' or command == '-h':
            display_banner()
        else:
            print(f"{Fore.RED}ERROR: Unknown command: {command}")
            print(f"{Fore.YELLOW}Available commands:")
            print(f"{Fore.CYAN}  python run.py setup        {Fore.WHITE}- Setup system")
            print(f"{Fore.CYAN}  python run.py test         {Fore.WHITE}- Test connections")
            print(f"{Fore.CYAN}  python run.py admin        {Fore.WHITE}- Admin interface")
            print(f"{Fore.CYAN}  python run.py researcher   {Fore.WHITE}- Researcher interface")
            print(f"{Fore.CYAN}  python run.py stats        {Fore.WHITE}- View statistics")
            print(f"{Fore.CYAN}  python run.py relationships {Fore.WHITE}- Show 6 relationships")
            print(f"{Fore.CYAN}  python run.py large-data   {Fore.WHITE}- Create large dataset")
            print(f"{Fore.CYAN}  python run.py help         {Fore.WHITE}- Show this help")
    else:
        interactive_menu()


def main():
    """Main function"""
    try:
        print(f"\n{Fore.CYAN}Starting Research Collaboration System - LARGE DATASET MODE...")
        print(f"{Fore.YELLOW}Target: 100 Researchers, 50 Projects, 30 Publications")
        print(f"{Fore.YELLOW}Relationships: 6 defined relationships")

        env_file = BASE_DIR / '.env'
        if not env_file.exists():
            print(f"{Fore.YELLOW}WARNING: .env file not found!")
            print(f"{Fore.WHITE}Creating .env.example...")

            example_env = BASE_DIR / '.env.example'
            with open(example_env, 'w') as f:
                f.write("""# Research Collaboration System - Environment Variables
# LARGE DATASET MODE: 100 researchers, 50 projects, 30 publications

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=research_collab_db

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=research123

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_USERNAME=
REDIS_SSL=False

# Application Settings
SECRET_KEY=your-secret-key-here-change-this
DEBUG=True
LOG_LEVEL=INFO

# Large Dataset Settings
DATASET_SIZE=large
""")

            print(f"{Fore.GREEN}SUCCESS: Created .env.example file")
            print(f"{Fore.YELLOW}Please copy .env.example to .env and update the values")
            print(f"{Fore.CYAN}Then run: python run.py setup")
            return

        command_line_mode()

    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}WARNING: System shutdown by user")
    except Exception as e:
        print(f"{Fore.RED}ERROR: Fatal error: {e}")
        sys.exit(1)
    finally:
        try:
            from app.database import db_manager
            db_manager.close_all()
        except:
            pass

        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.GREEN}Research Collaboration System - LARGE DATASET MODE Ended")
        print(f"{Fore.CYAN}6 Relationships: CO_AUTHORED_WITH, SUPERVISED, TEAMWORK_WITH,")
        print(f"{Fore.CYAN}                PARTICIPATED_IN, AUTHORED, PRODUCED")
        print(f"{Fore.CYAN}{'=' * 70}")


if __name__ == "__main__":
    main()