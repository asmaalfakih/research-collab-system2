#!/usr/bin/env python3
"""
Simple delete tool for Research Collaboration System
Direct MongoDB operations to fix deletion issues
"""

import sys
from pathlib import Path
from colorama import init, Fore, Style
from bson import ObjectId
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

init(autoreset=True)


def simple_delete_researcher(email: str):
    """Simple direct delete from MongoDB only"""
    print(f"\n{Fore.RED}{'=' * 70}")
    print(f"{Fore.YELLOW}SIMPLE DELETE - RESEARCHER")
    print(f"{Fore.RED}{'=' * 70}")

    try:
        from app.database.mongodb import mongodb

        # Find researcher
        researcher = mongodb.db.researchers.find_one({'email': email})
        if not researcher:
            print(f"{Fore.RED}ERROR: No researcher with email: {email}")
            return False

        researcher_id = str(researcher['_id'])
        name = researcher.get('name', 'Unknown')

        print(f"{Fore.WHITE}Found researcher: {name}")
        print(f"{Fore.WHITE}ID: {researcher_id}")
        print(f"{Fore.WHITE}Email: {email}")

        confirm = input(f"\n{Fore.RED}Type 'YES DELETE' to confirm: ").strip()
        if confirm != 'YES DELETE':
            print(f"{Fore.YELLOW}Cancelled")
            return False

        # SIMPLE DELETE - Only MongoDB
        new_email = f"{email}_DELETED_{int(datetime.utcnow().timestamp())}"

        result = mongodb.db.researchers.update_one(
            {'_id': ObjectId(researcher_id)},
            {'$set': {
                'profile_status': 'deleted',
                'updated_at': datetime.utcnow(),
                'email': new_email
            }}
        )

        if result.modified_count > 0:
            print(f"{Fore.GREEN}SUCCESS: Researcher '{name}' marked as deleted")
            print(f"{Fore.WHITE}New email in system: {new_email}")
            return True
        else:
            print(f"{Fore.RED}ERROR: Failed to update researcher")
            return False

    except Exception as e:
        print(f"{Fore.RED}ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def simple_delete_project(title: str):
    """Simple direct delete project"""
    print(f"\n{Fore.RED}{'=' * 70}")
    print(f"{Fore.YELLOW}SIMPLE DELETE - PROJECT")
    print(f"{Fore.RED}{'=' * 70}")

    try:
        from app.database.mongodb import mongodb

        # Find project
        project = mongodb.db.projects.find_one({'title': title})
        if not project:
            print(f"{Fore.RED}ERROR: No project with title: {title}")
            return False

        project_id = str(project['_id'])

        print(f"{Fore.WHITE}Found project: {project.get('title', 'Unknown')}")
        print(f"{Fore.WHITE}ID: {project_id}")

        confirm = input(f"\n{Fore.RED}Type 'YES DELETE' to confirm: ").strip()
        if confirm != 'YES DELETE':
            print(f"{Fore.YELLOW}Cancelled")
            return False

        # Delete project
        result = mongodb.db.projects.delete_one({'_id': ObjectId(project_id)})

        if result.deleted_count > 0:
            print(f"{Fore.GREEN}SUCCESS: Project deleted")
            return True
        else:
            print(f"{Fore.RED}ERROR: Failed to delete project")
            return False

    except Exception as e:
        print(f"{Fore.RED}ERROR: {str(e)}")
        return False


def simple_delete_publication(title: str):
    """Simple direct delete publication"""
    print(f"\n{Fore.RED}{'=' * 70}")
    print(f"{Fore.YELLOW}SIMPLE DELETE - PUBLICATION")
    print(f"{Fore.RED}{'=' * 70}")

    try:
        from app.database.mongodb import mongodb

        # Find publication
        publication = mongodb.db.publications.find_one({'title': title})
        if not publication:
            print(f"{Fore.RED}ERROR: No publication with title: {title}")
            return False

        publication_id = str(publication['_id'])

        print(f"{Fore.WHITE}Found publication: {publication.get('title', 'Unknown')}")
        print(f"{Fore.WHITE}ID: {publication_id}")

        confirm = input(f"\n{Fore.RED}Type 'YES DELETE' to confirm: ").strip()
        if confirm != 'YES DELETE':
            print(f"{Fore.YELLOW}Cancelled")
            return False

        # Delete publication
        result = mongodb.db.publications.delete_one({'_id': ObjectId(publication_id)})

        if result.deleted_count > 0:
            print(f"{Fore.GREEN}SUCCESS: Publication deleted")
            return True
        else:
            print(f"{Fore.RED}ERROR: Failed to delete publication")
            return False

    except Exception as e:
        print(f"{Fore.RED}ERROR: {str(e)}")
        return False


def main():
    """Main menu"""
    print(f"{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.YELLOW}SIMPLE DELETE TOOL - RESEARCH COLLABORATION SYSTEM")
    print(f"{Fore.CYAN}{'=' * 70}")

    print(f"\n{Fore.YELLOW}Options:")
    print(f"{Fore.GREEN}[1]{Fore.WHITE} Delete researcher by email")
    print(f"{Fore.GREEN}[2]{Fore.WHITE} Delete project by title")
    print(f"{Fore.GREEN}[3]{Fore.WHITE} Delete publication by title")
    print(f"{Fore.GREEN}[0]{Fore.WHITE} Exit")

    choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

    if choice == '1':
        email = input(f"{Fore.WHITE}Enter researcher email: ").strip()
        if email:
            simple_delete_researcher(email)

    elif choice == '2':
        title = input(f"{Fore.WHITE}Enter project title: ").strip()
        if title:
            simple_delete_project(title)

    elif choice == '3':
        title = input(f"{Fore.WHITE}Enter publication title: ").strip()
        if title:
            simple_delete_publication(title)

    elif choice == '0':
        print(f"{Fore.YELLOW}Exiting...")

    else:
        print(f"{Fore.RED}Invalid choice")


if __name__ == "__main__":
    main()