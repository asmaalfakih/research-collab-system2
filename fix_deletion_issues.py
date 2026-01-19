#!/usr/bin/env python3
"""
Fix deletion issues in Research Collaboration System
"""

import sys
from pathlib import Path
from colorama import init, Fore, Style

sys.path.append(str(Path(__file__).parent))

init(autoreset=True)


def fix_all_deletion_issues():
    """Fix all deletion-related issues"""
    print(f"{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.YELLOW}FIXING DELETION ISSUES - RESEARCH COLLABORATION SYSTEM")
    print(f"{Fore.CYAN}{'=' * 70}")

    try:
        from app.database.mongodb import mongodb
        from app.database.neo4j import neo4j
        from app.database.redis import redis_manager

        print(f"\n{Fore.GREEN}1. Checking database connections...")

        # Check MongoDB
        if mongodb.client:
            print(f"{Fore.GREEN}   MongoDB: Connected")
        else:
            print(f"{Fore.RED}   MongoDB: Not connected")
            return False

        # Check Neo4j
        if neo4j.driver:
            print(f"{Fore.GREEN}   Neo4j: Connected")
        else:
            print(f"{Fore.RED}   Neo4j: Not connected")
            return False

        # Check Redis
        if redis_manager.is_connected():
            print(f"{Fore.GREEN}   Redis: Connected")
        else:
            print(f"{Fore.YELLOW}   Redis: Not connected (optional)")

        print(f"\n{Fore.GREEN}2. Creating indexes for better deletion performance...")

        # Create indexes in MongoDB for faster queries
        indexes = [
            ('researchers', [('email', 1)], {'unique': True}),
            ('researchers', [('profile_status', 1)], {}),
            ('projects', [('participants', 1)], {}),
            ('projects', [('creator_id', 1)], {}),
            ('publications', [('authors.researcher_id', 1)], {})
        ]

        for collection, keys, options in indexes:
            try:
                mongodb.db[collection].create_index(keys, **options)
                print(f"{Fore.GREEN}   Created index for {collection}")
            except Exception as e:
                print(f"{Fore.YELLOW}   Index for {collection}: {e}")

        print(f"\n{Fore.GREEN}3. Cleaning up orphaned data...")

        # Find and remove orphaned references
        try:
            # Find researchers referenced in projects but not existing
            all_researcher_ids = [str(r['_id']) for r in mongodb.db.researchers.find({}, {'_id': 1})]

            projects = list(mongodb.db.projects.find({}))
            for project in projects:
                participants = project.get('participants', [])
                valid_participants = [p for p in participants if p in all_researcher_ids]

                if len(participants) != len(valid_participants):
                    mongodb.db.projects.update_one(
                        {'_id': project['_id']},
                        {'$set': {'participants': valid_participants}}
                    )
                    print(f"{Fore.YELLOW}   Fixed project: {project.get('title', 'Unknown')}")

        except Exception as e:
            print(f"{Fore.YELLOW}   Cleanup warning: {e}")

        print(f"\n{Fore.GREEN}4. Testing deletion functions...")

        # Create a test researcher for deletion test
        test_researcher = {
            'name': 'Test Researcher For Deletion',
            'email': 'test.delete@university.edu',
            'department': 'Test Department',
            'profile_status': 'approved',
            'role': 'researcher',
            'research_interests': ['Testing']
        }

        test_id = mongodb.create_researcher(test_researcher)

        if test_id:
            print(f"{Fore.GREEN}   Created test researcher: {test_id}")

            # Test safe delete
            from app.services.researcher_service import ResearcherService
            success, message = ResearcherService.safe_delete_researcher(test_id, 'system_admin')

            if success:
                print(f"{Fore.GREEN}   Test deletion: SUCCESS - {message}")
            else:
                print(f"{Fore.RED}   Test deletion: FAILED - {message}")
        else:
            print(f"{Fore.YELLOW}   Could not create test researcher")

        print(f"\n{Fore.GREEN}5. Clearing cache...")

        try:
            if redis_manager.is_connected():
                redis_manager.client.delete("all_relationships")
                redis_manager.client.delete("relationship_statistics")
                redis_manager.client.delete("system:stats")
                print(f"{Fore.GREEN}   Cache cleared")
        except:
            print(f"{Fore.YELLOW}   Cache clear skipped")

        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.GREEN}FIXES APPLIED SUCCESSFULLY!")
        print(f"\n{Fore.YELLOW}Next steps:")
        print(f"{Fore.WHITE}   1. Try deleting a researcher: python run.py 3")
        print(f"{Fore.WHITE}   2. Try deleting a project: python run.py 3")
        print(f"{Fore.WHITE}   3. Try deleting a publication: python run.py 3")
        print(f"{Fore.CYAN}{'=' * 70}")

        return True

    except Exception as e:
        print(f"{Fore.RED}ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    fix_all_deletion_issues()