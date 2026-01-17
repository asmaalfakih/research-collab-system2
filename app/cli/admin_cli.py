#!/usr/bin/env python3
"""
CLI Interface for Administrators
"""

import sys
from pathlib import Path
from colorama import init, Fore, Style
import click
from tabulate import tabulate
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.auth_service import AuthService
from app.services.researcher_service import ResearcherService
from app.services.collaboration_service import CollaborationService
from app.services.project_service import ProjectService
from app.services.publication_service import PublicationService
from app.database.mongodb import mongodb
from app.database.redis import redis_manager

init(autoreset=True)


class AdminCLI:
    def __init__(self):
        self.current_session = None
        self.current_user = None

    def login(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ADMIN LOGIN - AUTO LOGIN")
        print(f"{Fore.CYAN}{'=' * 50}")

        email = "admin@university.edu"
        password = "admin123"

        print(f"\n{Fore.WHITE}Using auto-generated credentials:")
        print(f"  Email: {email}")
        print(f"  Password: {'*' * len(password)}")

        success, session_id, user_data, message = AuthService.login(email, password)

        if success and user_data['role'] == 'admin':
            self.current_session = session_id
            self.current_user = user_data
            print(f"\n{Fore.GREEN}SUCCESS: {message}")
            print(f"{Fore.CYAN}Welcome, Administrator {user_data['name']}!")
            return True
        elif success:
            print(f"\n{Fore.RED}ERROR: Access denied. Admin privileges required.")
            return False
        else:
            print(f"\n{Fore.RED}ERROR: {message}")
            print(f"{Fore.YELLOW}Creating admin account automatically...")

            from app.models.researcher import Researcher

            admin_data = {
                'name': 'System Admin',
                'email': email,
                'password': Researcher.hash_password(password),
                'department': 'Administration',
                'profile_status': 'approved',
                'role': 'admin',
                'research_interests': ['System Management']
            }

            from app.database.neo4j import neo4j
            admin_id = mongodb.create_researcher(admin_data)

            if admin_id:
                neo4j.create_researcher_node({
                    'id': admin_id,
                    'name': admin_data['name'],
                    'email': admin_data['email'],
                    'department': admin_data['department'],
                    'profile_status': admin_data['profile_status']
                })

                print(f"{Fore.GREEN}SUCCESS: Admin account created!")

                success, session_id, user_data, message = AuthService.login(email, password)
                if success:
                    self.current_session = session_id
                    self.current_user = user_data
                    print(f"\n{Fore.GREEN}SUCCESS: Auto-login successful!")
                    return True

            return False

    def display_menu(self):
        menu = f"""
{Fore.CYAN}{'=' * 60}
{Fore.YELLOW}ADMIN DASHBOARD - {self.current_user['name'] if self.current_user else 'System'}
{Fore.CYAN}{'=' * 60}

{Fore.GREEN}[1]{Fore.WHITE} View System Statistics
{Fore.GREEN}[2]{Fore.WHITE} Manage Researchers
{Fore.GREEN}[3]{Fore.WHITE} Manage Projects
{Fore.GREEN}[4]{Fore.WHITE} Manage Publications
{Fore.GREEN}[5]{Fore.WHITE} Collaboration Analytics
{Fore.GREEN}[6]{Fore.WHITE} Monitor System Activity
{Fore.GREEN}[7]{Fore.WHITE} Manage All Relationships

{Fore.GREEN}[0]{Fore.WHITE} Logout & Exit
{Fore.CYAN}{'=' * 60}
        """
        print(menu)

    def view_system_stats(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}SYSTEM STATISTICS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}MONGODB DATABASE:")
        total_researchers = mongodb.db.researchers.count_documents({})
        approved_researchers = mongodb.db.researchers.count_documents({'profile_status': 'approved'})
        pending_researchers = mongodb.db.researchers.count_documents({'profile_status': 'pending'})
        total_projects = mongodb.db.projects.count_documents({})
        total_publications = mongodb.db.publications.count_documents({})

        print(f"{Fore.WHITE}   Total Researchers: {total_researchers}")
        print(f"   Approved Researchers: {approved_researchers}")
        print(f"   Pending Approvals: {pending_researchers}")
        print(f"   Total Projects: {total_projects}")
        print(f"   Total Publications: {total_publications}")

        print(f"\n{Fore.GREEN}RELATIONSHIPS:")
        collab_stats = CollaborationService.get_relationship_statistics()

        if collab_stats and 'relationship_counts' in collab_stats:
            rel_counts = collab_stats['relationship_counts']
            print(f"{Fore.WHITE}   SUPERVISES: {rel_counts.get('SUPERVISES', 0)}")
            print(f"   PARTICIPATED_IN: {rel_counts.get('PARTICIPATED_IN', 0)}")
            print(f"   TEAMWORK_WITH: {rel_counts.get('TEAMWORK_WITH', 0)}")
            print(f"   AUTHORED: {rel_counts.get('AUTHORED', 0)}")
            print(f"   CO_AUTHORED_WITH: {rel_counts.get('CO_AUTHORED_WITH', 0)}")
            print(f"   PRODUCED: {rel_counts.get('PRODUCED', 0)}")

        print(f"\n{Fore.GREEN}REDIS CACHE:")
        if redis_manager.is_connected():
            try:
                info = redis_manager.client.info()
                print(f"{Fore.WHITE}   Status: Connected")
                print(f"   Memory Used: {info.get('used_memory_human', 'N/A')}")
                print(f"   Connected Clients: {info.get('connected_clients', 0)}")
                print(f"   Total Keys: {info.get('db0', {}).get('keys', 0)}")
            except:
                print(f"{Fore.WHITE}   Status: Connected (detailed stats unavailable)")
        else:
            print(f"{Fore.RED}   Status: Disconnected")

    def manage_researchers(self):
        while True:
            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}MANAGE RESEARCHERS")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} View All Researchers")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} View Pending Approvals")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Update Researcher Status")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} View Researcher Details")
            print(f"{Fore.GREEN}[5]{Fore.WHITE} Delete Researcher")
            print(f"{Fore.GREEN}[6]{Fore.WHITE} Back to Main Menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ")

            if choice == '1':
                self.view_all_researchers()
            elif choice == '2':
                self.view_pending_approvals()
            elif choice == '3':
                self.update_researcher_status()
            elif choice == '4':
                self.view_researcher_details()
            elif choice == '5':
                self.delete_researcher()
            elif choice == '6':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def view_all_researchers(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ALL RESEARCHERS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            all_researchers = list(mongodb.db.researchers.find(
                {'profile_status': {'$ne': 'deleted'}}
            ).sort('name', 1))

            if not all_researchers:
                print(f"\n{Fore.YELLOW}WARNING: No researchers found")
                return

            table_data = []
            for i, researcher in enumerate(all_researchers, 1):
                researcher_id = str(researcher['_id'])
                stats = ResearcherService.get_researcher_statistics(researcher_id)

                table_data.append([
                    i,
                    researcher.get('name', 'N/A'),
                    researcher.get('email', 'N/A'),
                    researcher.get('department', 'N/A'),
                    researcher.get('profile_status', 'N/A'),
                    researcher.get('role', 'researcher'),
                    stats.get('projects_count', 0),
                    stats.get('publications_count', 0),
                    stats.get('coauthors_count', 0)
                ])

            headers = ['#', 'Name', 'Email', 'Department', 'Status', 'Role', 'Projects', 'Publications', 'Co-authors']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            print(f"\n{Fore.GREEN}Total researchers: {len(all_researchers)}")

        except Exception as e:
            print(f"{Fore.RED}ERROR: Error displaying researchers: {e}")

    def view_pending_approvals(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}PENDING APPROVALS")
        print(f"{Fore.CYAN}{'=' * 50}")

        pending_researchers = list(mongodb.db.researchers.find(
            {'profile_status': 'pending'}
        ).sort('created_at', 1))

        if not pending_researchers:
            print(f"\n{Fore.GREEN}SUCCESS: No pending approvals")
            return

        print(f"\n{Fore.YELLOW}Found {len(pending_researchers)} pending researcher(s):")

        table_data = []
        for i, researcher in enumerate(pending_researchers, 1):
            table_data.append([
                i,
                researcher['name'],
                researcher['email'],
                researcher['department'],
                ', '.join(researcher['research_interests'][:3]),
                researcher['created_at'].strftime('%Y-%m-%d') if hasattr(researcher['created_at'], 'strftime') else str(
                    researcher['created_at'])
            ])

        headers = ['#', 'Name', 'Email', 'Department', 'Interests', 'Registered']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        print(f"\n{Fore.GREEN}[A]{Fore.WHITE} Approve All")
        print(f"{Fore.GREEN}[S]{Fore.WHITE} Select to Approve")
        print(f"{Fore.GREEN}[R]{Fore.WHITE} Return")

        choice = input(f"\n{Fore.YELLOW}Select option: ").upper()

        if choice == 'A':
            for researcher in pending_researchers:
                researcher_id = str(researcher['_id'])
                success, message = ResearcherService.update_researcher_status(
                    researcher_id, 'approved', self.current_user['id']
                )
                if success:
                    print(f"{Fore.GREEN}Approved: {researcher['name']}")
                else:
                    print(f"{Fore.RED}Failed: {researcher['name']} - {message}")
        elif choice == 'S':
            selection = input("Enter numbers to approve (comma-separated): ")
            indices = [int(idx.strip()) - 1 for idx in selection.split(',') if idx.strip().isdigit()]
            for idx in indices:
                if 0 <= idx < len(pending_researchers):
                    researcher = pending_researchers[idx]
                    researcher_id = str(researcher['_id'])
                    success, message = ResearcherService.update_researcher_status(
                        researcher_id, 'approved', self.current_user['id']
                    )
                    if success:
                        print(f"{Fore.GREEN}Approved: {researcher['name']}")
                    else:
                        print(f"{Fore.RED}Failed: {researcher['name']} - {message}")

    def update_researcher_status(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}UPDATE RESEARCHER STATUS")
        print(f"{Fore.CYAN}{'=' * 50}")

        email = input(f"{Fore.WHITE}Enter researcher email: ").strip()
        if not email:
            print(f"{Fore.RED}ERROR: Email required")
            return

        researcher = mongodb.db.researchers.find_one({'email': email})
        if not researcher:
            print(f"{Fore.RED}ERROR: Researcher not found")
            return

        researcher_id = str(researcher['_id'])
        print(f"\n{Fore.WHITE}Current Status: {Fore.YELLOW}{researcher.get('profile_status', 'N/A')}")
        print(f"{Fore.WHITE}Name: {researcher.get('name', 'N/A')}")

        print(f"\n{Fore.GREEN}New Status:")
        print(f"{Fore.WHITE}[1] approved")
        print(f"{Fore.WHITE}[2] pending")
        print(f"{Fore.WHITE}[3] rejected")
        print(f"{Fore.WHITE}[4] suspended")

        status_choice = input(f"\n{Fore.YELLOW}Select status: ").strip()
        status_map = {'1': 'approved', '2': 'pending', '3': 'rejected', '4': 'suspended'}

        if status_choice not in status_map:
            print(f"{Fore.RED}ERROR: Invalid choice")
            return

        new_status = status_map[status_choice]
        success, message = ResearcherService.update_researcher_status(
            researcher_id, new_status, self.current_user['id']
        )

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def view_researcher_details(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}VIEW RESEARCHER DETAILS")
        print(f"{Fore.CYAN}{'=' * 50}")

        email = input(f"{Fore.WHITE}Enter researcher email: ").strip()
        if not email:
            print(f"{Fore.RED}ERROR: Email required")
            return

        researcher = mongodb.db.researchers.find_one({'email': email})
        if not researcher:
            print(f"{Fore.RED}ERROR: Researcher not found")
            return

        researcher_id = str(researcher['_id'])
        details = ResearcherService.get_researcher_details(researcher_id)

        if not details:
            print(f"{Fore.RED}ERROR: Could not get researcher details")
            return

        print(f"\n{Fore.GREEN}BASIC INFORMATION:")
        basic_info = details.get('researcher_info', {})
        print(f"{Fore.WHITE}   Name: {basic_info.get('name', 'N/A')}")
        print(f"   Email: {basic_info.get('email', 'N/A')}")
        print(f"   Department: {basic_info.get('department', 'N/A')}")
        print(f"   Status: {basic_info.get('profile_status', 'N/A')}")
        print(f"   Role: {basic_info.get('role', 'researcher')}")
        print(f"   Research Interests: {', '.join(basic_info.get('research_interests', []))}")

        print(f"\n{Fore.GREEN}STATISTICS:")
        print(f"{Fore.WHITE}   Projects: {details.get('projects_count', 0)}")
        print(f"   Publications: {details.get('publications_count', 0)}")
        print(f"   Collaborators: {details.get('collaborators_count', 0)}")
        print(f"   Teamwork Partners: {details.get('teamwork_count', 0)}")

        print(f"\n{Fore.GREEN}TOP COLLABORATORS:")
        collab_summary = CollaborationService.get_researcher_collaboration_summary(researcher_id)
        if collab_summary and 'top_collaborators' in collab_summary:
            for i, collab in enumerate(collab_summary['top_collaborators'][:5], 1):
                print(
                    f"{Fore.WHITE}   {i}. {collab.get('other_name', 'Unknown')} - {collab.get('collaboration_count', 0)} collaborations")

    def delete_researcher(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}DELETE RESEARCHER")
        print(f"{Fore.CYAN}{'=' * 50}")

        email = input(f"{Fore.WHITE}Enter researcher email: ").strip()
        if not email:
            print(f"{Fore.RED}ERROR: Email required")
            return

        researcher = mongodb.db.researchers.find_one({'email': email})
        if not researcher:
            print(f"{Fore.RED}ERROR: Researcher not found")
            return

        print(f"\n{Fore.RED}WARNING: You are about to delete researcher:")
        print(f"{Fore.WHITE}Name: {researcher.get('name', 'N/A')}")
        print(f"Email: {researcher.get('email', 'N/A')}")
        print(f"Department: {researcher.get('department', 'N/A')}")
        print(f"Status: {researcher.get('profile_status', 'N/A')}")

        confirm = input(f"\n{Fore.RED}Type 'DELETE' to confirm: ").strip()
        if confirm != 'DELETE':
            print(f"{Fore.YELLOW}Cancelled")
            return

        researcher_id = str(researcher['_id'])
        success, message = ResearcherService.delete_researcher(researcher_id, self.current_user['id'])

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def manage_projects(self):
        while True:
            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}MANAGE PROJECTS")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} View All Projects")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} View Project Details")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Update Project Status")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Delete Project")
            print(f"{Fore.GREEN}[5]{Fore.WHITE} Back to Main Menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ")

            if choice == '1':
                self.view_all_projects()
            elif choice == '2':
                self.view_project_details()
            elif choice == '3':
                self.update_project_status()
            elif choice == '4':
                self.delete_project()
            elif choice == '5':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def view_all_projects(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ALL PROJECTS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            all_projects = list(mongodb.db.projects.find().sort('created_at', -1))

            if not all_projects:
                print(f"\n{Fore.YELLOW}WARNING: No projects found")
                return

            table_data = []
            for i, project in enumerate(all_projects, 1):
                project_id = str(project['_id'])
                stats = ProjectService.get_project_statistics(project_id)

                table_data.append([
                    i,
                    project.get('title', 'N/A')[:40],
                    project.get('creator_name', 'N/A')[:20],
                    project.get('status', 'N/A'),
                    len(project.get('participants', [])),
                    stats.get('publications_count', 0),
                    project.get('created_at').strftime('%Y-%m-%d') if hasattr(project.get('created_at'),
                                                                              'strftime') else 'N/A'
                ])

            headers = ['#', 'Title', 'Creator', 'Status', 'Participants', 'Publications', 'Created']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            print(f"\n{Fore.GREEN}Total projects: {len(all_projects)}")

        except Exception as e:
            print(f"{Fore.RED}ERROR: Error displaying projects: {e}")

    def view_project_details(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}VIEW PROJECT DETAILS")
        print(f"{Fore.CYAN}{'=' * 50}")

        title = input(f"{Fore.WHITE}Enter project title (or part of it): ").strip()
        if not title:
            print(f"{Fore.RED}ERROR: Title required")
            return

        projects = list(mongodb.db.projects.find(
            {'title': {'$regex': title, '$options': 'i'}}
        ).limit(10))

        if not projects:
            print(f"{Fore.RED}ERROR: No projects found")
            return

        if len(projects) > 1:
            print(f"\n{Fore.YELLOW}Multiple projects found:")
            for i, project in enumerate(projects, 1):
                print(f"{Fore.WHITE}  {i}. {project.get('title', 'N/A')} - {project.get('status', 'N/A')}")

            selection = input(f"\n{Fore.YELLOW}Select project number: ").strip()
            if not selection.isdigit() or int(selection) < 1 or int(selection) > len(projects):
                print(f"{Fore.RED}ERROR: Invalid selection")
                return
            project = projects[int(selection) - 1]
        else:
            project = projects[0]

        project_id = str(project['_id'])
        details = ProjectService.get_project_details(project_id)

        if not details:
            print(f"{Fore.RED}ERROR: Could not get project details")
            return

        print(f"\n{Fore.GREEN}PROJECT INFORMATION:")
        project_info = details.get('project_info', {})
        print(f"{Fore.WHITE}   Title: {project_info.get('title', 'N/A')}")
        print(f"   Creator: {project_info.get('creator_name', 'N/A')}")
        print(f"   Status: {project_info.get('status', 'N/A')}")
        print(f"   Research Area: {project_info.get('research_area', 'N/A')}")
        print(f"   Start Date: {project_info.get('start_date', 'N/A')}")
        print(f"   End Date: {project_info.get('end_date', 'N/A')}")
        print(f"   Participants: {details.get('participants_count', 0)}")
        print(f"   Publications: {details.get('publications_count', 0)}")

        if details.get('supervisor'):
            print(f"   Supervisor: {details['supervisor'].get('name', 'N/A')}")

        if details.get('participants'):
            print(f"\n{Fore.GREEN}PARTICIPANTS:")
            for participant in details['participants'][:10]:
                print(f"{Fore.WHITE}   - {participant.get('name', 'N/A')} ({participant.get('role', 'participant')})")

    def update_project_status(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}UPDATE PROJECT STATUS")
        print(f"{Fore.CYAN}{'=' * 50}")

        title = input(f"{Fore.WHITE}Enter project title: ").strip()
        if not title:
            print(f"{Fore.RED}ERROR: Title required")
            return

        project = mongodb.db.projects.find_one({'title': title})
        if not project:
            print(f"{Fore.RED}ERROR: Project not found")
            return

        project_id = str(project['_id'])
        print(f"\n{Fore.WHITE}Current Status: {Fore.YELLOW}{project.get('status', 'N/A')}")
        print(f"{Fore.WHITE}Title: {project.get('title', 'N/A')}")

        print(f"\n{Fore.GREEN}New Status:")
        print(f"{Fore.WHITE}[1] active")
        print(f"{Fore.WHITE}[2] completed")
        print(f"{Fore.WHITE}[3] pending")
        print(f"{Fore.WHITE}[4] cancelled")

        status_choice = input(f"\n{Fore.YELLOW}Select status: ").strip()
        status_map = {'1': 'active', '2': 'completed', '3': 'pending', '4': 'cancelled'}

        if status_choice not in status_map:
            print(f"{Fore.RED}ERROR: Invalid choice")
            return

        new_status = status_map[status_choice]
        success, message = ProjectService.update_project_status(
            project_id, new_status, self.current_user['id']
        )

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def delete_project(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}DELETE PROJECT")
        print(f"{Fore.CYAN}{'=' * 50}")

        title = input(f"{Fore.WHITE}Enter project title: ").strip()
        if not title:
            print(f"{Fore.RED}ERROR: Title required")
            return

        project = mongodb.db.projects.find_one({'title': title})
        if not project:
            print(f"{Fore.RED}ERROR: Project not found")
            return

        print(f"\n{Fore.RED}WARNING: You are about to delete project:")
        print(f"{Fore.WHITE}Title: {project.get('title', 'N/A')}")
        print(f"Creator: {project.get('creator_name', 'N/A')}")
        print(f"Status: {project.get('status', 'N/A')}")
        print(f"Participants: {len(project.get('participants', []))}")

        confirm = input(f"\n{Fore.RED}Type 'DELETE' to confirm: ").strip()
        if confirm != 'DELETE':
            print(f"{Fore.YELLOW}Cancelled")
            return

        project_id = str(project['_id'])
        success, message = ProjectService.delete_project(project_id, self.current_user['id'])

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def manage_publications(self):
        while True:
            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}MANAGE PUBLICATIONS")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} View All Publications")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} View Publication Details")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Delete Publication")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Back to Main Menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ")

            if choice == '1':
                self.view_all_publications()
            elif choice == '2':
                self.view_publication_details()
            elif choice == '3':
                self.delete_publication()
            elif choice == '4':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def view_all_publications(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ALL PUBLICATIONS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            all_publications = list(mongodb.db.publications.find().sort('year', -1).limit(50))

            if not all_publications:
                print(f"\n{Fore.YELLOW}WARNING: No publications found")
                return

            table_data = []
            for i, pub in enumerate(all_publications, 1):
                pub_id = str(pub['_id'])
                authors = pub.get('authors', [])
                author_names = []
                for author in authors[:2]:
                    if isinstance(author, dict):
                        author_names.append(author.get('name', 'Unknown'))

                table_data.append([
                    i,
                    pub.get('title', 'N/A')[:50],
                    ', '.join(author_names),
                    pub.get('year', 'N/A'),
                    pub.get('journal', 'N/A')[:20],
                    pub.get('citation_count', 0),
                    len(authors)
                ])

            headers = ['#', 'Title', 'Authors', 'Year', 'Journal', 'Citations', 'Authors']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            print(f"\n{Fore.GREEN}Showing {len(all_publications)} publications")

        except Exception as e:
            print(f"{Fore.RED}ERROR: Error displaying publications: {e}")

    def view_publication_details(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}VIEW PUBLICATION DETAILS")
        print(f"{Fore.CYAN}{'=' * 50}")

        title = input(f"{Fore.WHITE}Enter publication title (or part of it): ").strip()
        if not title:
            print(f"{Fore.RED}ERROR: Title required")
            return

        publications = list(mongodb.db.publications.find(
            {'title': {'$regex': title, '$options': 'i'}}
        ).limit(10))

        if not publications:
            print(f"{Fore.RED}ERROR: No publications found")
            return

        if len(publications) > 1:
            print(f"\n{Fore.YELLOW}Multiple publications found:")
            for i, pub in enumerate(publications, 1):
                print(f"{Fore.WHITE}  {i}. {pub.get('title', 'N/A')[:60]} - {pub.get('year', 'N/A')}")

            selection = input(f"\n{Fore.YELLOW}Select publication number: ").strip()
            if not selection.isdigit() or int(selection) < 1 or int(selection) > len(publications):
                print(f"{Fore.RED}ERROR: Invalid selection")
                return
            publication = publications[int(selection) - 1]
        else:
            publication = publications[0]

        publication_id = str(publication['_id'])
        details = PublicationService.get_publication_details(publication_id)

        if not details:
            print(f"{Fore.RED}ERROR: Could not get publication details")
            return

        print(f"\n{Fore.GREEN}PUBLICATION INFORMATION:")
        pub_info = details.get('publication_info', {})
        print(f"{Fore.WHITE}   Title: {pub_info.get('title', 'N/A')}")
        print(f"   Year: {pub_info.get('year', 'N/A')}")
        print(f"   Journal: {pub_info.get('journal', 'N/A')}")
        print(f"   DOI: {pub_info.get('doi', 'N/A')}")
        print(f"   Status: {pub_info.get('status', 'N/A')}")
        print(f"   Citations: {pub_info.get('citation_count', 0)}")
        print(f"   Views: {pub_info.get('views', 0)}")
        print(f"   Downloads: {pub_info.get('downloads', 0)}")

        if details.get('authors'):
            print(f"\n{Fore.GREEN}AUTHORS ({len(details['authors'])}):")
            for author in details['authors']:
                role = "First Author" if author.get('order') == 1 else f"Co-author ({author.get('order')})"
                print(f"{Fore.WHITE}   - {author.get('name', 'N/A')} ({role})")

        if details.get('projects'):
            print(f"\n{Fore.GREEN}RELATED PROJECTS ({len(details['projects'])}):")
            for project in details['projects']:
                print(f"{Fore.WHITE}   - {project.get('title', 'N/A')} ({project.get('status', 'N/A')})")

    def delete_publication(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}DELETE PUBLICATION")
        print(f"{Fore.CYAN}{'=' * 50}")

        title = input(f"{Fore.WHITE}Enter publication title: ").strip()
        if not title:
            print(f"{Fore.RED}ERROR: Title required")
            return

        publication = mongodb.db.publications.find_one({'title': title})
        if not publication:
            print(f"{Fore.RED}ERROR: Publication not found")
            return

        print(f"\n{Fore.RED}WARNING: You are about to delete publication:")
        print(f"{Fore.WHITE}Title: {publication.get('title', 'N/A')}")
        print(f"Year: {publication.get('year', 'N/A')}")
        print(f"Journal: {publication.get('journal', 'N/A')}")
        print(f"Authors: {len(publication.get('authors', []))}")

        confirm = input(f"\n{Fore.RED}Type 'DELETE' to confirm: ").strip()
        if confirm != 'DELETE':
            print(f"{Fore.YELLOW}Cancelled")
            return

        publication_id = str(publication['_id'])
        success, message = PublicationService.delete_publication(publication_id, self.current_user['id'])

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def view_collaboration_analytics(self):
        while True:
            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}COLLABORATION ANALYTICS")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} Most Collaborative Pairs")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} Most Active Teams")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Network Statistics")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Relationship Types Summary")
            print(f"{Fore.GREEN}[5]{Fore.WHITE} Back to Main Menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ")

            if choice == '1':
                self.view_most_collaborative_pairs()
            elif choice == '2':
                self.view_most_active_teams()
            elif choice == '3':
                self.view_network_statistics()
            elif choice == '4':
                self.view_relationship_summary()
            elif choice == '5':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def view_most_collaborative_pairs(self):
        try:
            limit_input = input(f"\n{Fore.WHITE}Number of pairs to show (default: 10): ").strip()
            limit = int(limit_input) if limit_input else 10
        except:
            limit = 10

        pairs = CollaborationService.get_most_collaborative_pairs(limit)

        if not pairs:
            print(f"\n{Fore.YELLOW}WARNING: No collaboration pairs found")
            return

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.YELLOW}MOST COLLABORATIVE PAIRS (Top {len(pairs)})")
        print(f"{Fore.CYAN}{'=' * 80}")

        table_data = []
        for i, pair in enumerate(pairs, 1):
            table_data.append([
                i,
                f"{pair['researcher1_name']}",
                f"{pair['researcher2_name']}",
                pair['collaboration_count'],
                pair.get('publications_count', 0),
                pair.get('last_collaboration', 'N/A')
            ])

        headers = ['#', 'Researcher 1', 'Researcher 2', 'Collaborations', 'Publications', 'Last Collaboration']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def view_most_active_teams(self):
        try:
            limit_input = input(f"\n{Fore.WHITE}Number of teams to show (default: 10): ").strip()
            limit = int(limit_input) if limit_input else 10
        except:
            limit = 10

        teams = CollaborationService.get_most_active_teams(limit)

        if not teams:
            print(f"\n{Fore.YELLOW}WARNING: No active teams found")
            return

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.YELLOW}MOST ACTIVE TEAMS (Top {len(teams)})")
        print(f"{Fore.CYAN}{'=' * 80}")

        table_data = []
        for i, team in enumerate(teams, 1):
            table_data.append([
                i,
                f"{team['researcher1_name']}",
                f"{team['researcher2_name']}",
                team['collaboration_count'],
                team.get('projects_count', 0),
                team.get('last_collaboration', 'N/A')
            ])

        headers = ['#', 'Researcher 1', 'Researcher 2', 'Collaborations', 'Projects', 'Last Collaboration']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def view_network_statistics(self):
        stats = CollaborationService.get_relationship_statistics()

        if not stats:
            print(f"\n{Fore.YELLOW}WARNING: No network statistics available")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}NETWORK STATISTICS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}Database Totals:")
        print(f"{Fore.WHITE}   Total Researchers: {stats.get('total_researchers', 'N/A')}")
        print(f"   Total Projects: {stats.get('total_projects', 'N/A')}")
        print(f"   Total Publications: {stats.get('total_publications', 'N/A')}")

        print(f"\n{Fore.GREEN}Relationship Statistics:")
        if 'relationship_counts' in stats:
            rel_counts = stats['relationship_counts']
            total_relationships = sum(rel_counts.values())
            print(f"{Fore.WHITE}   Total Relationships: {total_relationships}")
            for rel_type, count in rel_counts.items():
                if count > 0:
                    percentage = (count / total_relationships * 100) if total_relationships > 0 else 0
                    print(f"   {rel_type}: {count} ({percentage:.1f}%)")

        print(f"\n{Fore.GREEN}Collaboration Metrics:")
        print(
            f"{Fore.WHITE}   Avg Collaborations per Researcher: {stats.get('average_collaborations_per_researcher', 0):.2f}")

    def view_relationship_summary(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RELATIONSHIP TYPES SUMMARY")
        print(f"{Fore.CYAN}{'=' * 50}")

        relationship_types = [
            'SUPERVISES',
            'PARTICIPATED_IN',
            'TEAMWORK_WITH',
            'AUTHORED',
            'CO_AUTHORED_WITH',
            'PRODUCED'
        ]

        for rel_type in relationship_types:
            relationships = CollaborationService.get_relationships_by_type(rel_type)
            if relationships:
                print(f"\n{Fore.GREEN}{rel_type}: {len(relationships)} relationships")
                for i, rel in enumerate(relationships[:3], 1):
                    if 'researcher1_name' in rel and 'researcher2_name' in rel:
                        print(f"{Fore.WHITE}   {i}. {rel['researcher1_name']} - {rel['researcher2_name']}")
                    elif 'researcher_name' in rel and 'project_title' in rel:
                        print(f"{Fore.WHITE}   {i}. {rel['researcher_name']} -> {rel['project_title']}")
                    elif 'project_title' in rel and 'publication_title' in rel:
                        print(f"{Fore.WHITE}   {i}. {rel['project_title']} -> {rel['publication_title']}")
                if len(relationships) > 3:
                    print(f"{Fore.WHITE}   ... and {len(relationships) - 3} more")

    def manage_all_relationships(self):
        while True:
            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}MANAGE ALL RELATIONSHIPS")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} View All Relationships")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} View by Relationship Type")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} View Researcher Relationships")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Delete Relationship")
            print(f"{Fore.GREEN}[5]{Fore.WHITE} Back to Main Menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ")

            if choice == '1':
                self.view_all_relationships()
            elif choice == '2':
                self.view_relationships_by_type()
            elif choice == '3':
                self.view_researcher_relationships()
            elif choice == '4':
                self.delete_relationship()
            elif choice == '5':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def view_all_relationships(self):
        relationships = CollaborationService.get_all_relationships()

        if not relationships:
            print(f"\n{Fore.YELLOW}WARNING: No relationships found")
            return

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.YELLOW}ALL RELATIONSHIPS ({len(relationships)})")
        print(f"{Fore.CYAN}{'=' * 80}")

        table_data = []
        for i, rel in enumerate(relationships[:20], 1):
            if 'researcher1_name' in rel and 'researcher2_name' in rel:
                table_data.append([
                    i,
                    rel.get('type', 'N/A'),
                    f"{rel['researcher1_name']}",
                    f"{rel['researcher2_name']}",
                    rel.get('collaboration_count', 1)
                ])
            elif 'researcher_name' in rel and 'project_title' in rel:
                table_data.append([
                    i,
                    rel.get('type', 'N/A'),
                    f"{rel['researcher_name']}",
                    f"{rel['project_title']}",
                    rel.get('role', 'N/A')
                ])
            elif 'project_title' in rel and 'publication_title' in rel:
                table_data.append([
                    i,
                    rel.get('type', 'N/A'),
                    f"{rel['project_title']}",
                    f"{rel['publication_title']}",
                    'N/A'
                ])

        headers = ['#', 'Type', 'From', 'To', 'Details']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        if len(relationships) > 20:
            print(f"\n{Fore.YELLOW}Showing 20 of {len(relationships)} relationships")

    def view_relationships_by_type(self):
        print(f"\n{Fore.GREEN}Relationship Types:")
        print(f"{Fore.WHITE}[1] SUPERVISES")
        print(f"{Fore.WHITE}[2] PARTICIPATED_IN")
        print(f"{Fore.WHITE}[3] TEAMWORK_WITH")
        print(f"{Fore.WHITE}[4] AUTHORED")
        print(f"{Fore.WHITE}[5] CO_AUTHORED_WITH")
        print(f"{Fore.WHITE}[6] PRODUCED")

        choice = input(f"\n{Fore.YELLOW}Select relationship type: ").strip()

        type_map = {
            '1': 'SUPERVISES',
            '2': 'PARTICIPATED_IN',
            '3': 'TEAMWORK_WITH',
            '4': 'AUTHORED',
            '5': 'CO_AUTHORED_WITH',
            '6': 'PRODUCED'
        }

        if choice not in type_map:
            print(f"{Fore.RED}ERROR: Invalid choice")
            return

        rel_type = type_map[choice]
        relationships = CollaborationService.get_relationships_by_type(rel_type)

        if not relationships:
            print(f"\n{Fore.YELLOW}WARNING: No {rel_type} relationships found")
            return

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.YELLOW}{rel_type} RELATIONSHIPS ({len(relationships)})")
        print(f"{Fore.CYAN}{'=' * 80}")

        if rel_type in ['CO_AUTHORED_WITH', 'TEAMWORK_WITH']:
            table_data = []
            for i, rel in enumerate(relationships[:15], 1):
                table_data.append([
                    i,
                    f"{rel['researcher1_name']}",
                    f"{rel['researcher2_name']}",
                    rel.get('collaboration_count', 1),
                    rel.get('last_collaboration', 'N/A')
                ])
            headers = ['#', 'Researcher 1', 'Researcher 2', 'Count', 'Last Collaboration']

        elif rel_type in ['SUPERVISES', 'PARTICIPATED_IN', 'AUTHORED']:
            table_data = []
            for i, rel in enumerate(relationships[:15], 1):
                if rel_type == 'AUTHORED':
                    table_data.append([
                        i,
                        f"{rel['researcher_name']}",
                        f"{rel['publication_title']}",
                        rel.get('author_order', 1),
                        'N/A'
                    ])
                else:
                    table_data.append([
                        i,
                        f"{rel['researcher_name']}",
                        f"{rel['project_title']}",
                        rel.get('role', 'participant'),
                        'N/A'
                    ])
            headers = ['#', 'Researcher', 'Target', 'Role/Order', 'Details']

        elif rel_type == 'PRODUCED':
            table_data = []
            for i, rel in enumerate(relationships[:15], 1):
                table_data.append([
                    i,
                    f"{rel['project_title']}",
                    f"{rel['publication_title']}",
                    'N/A',
                    'N/A'
                ])
            headers = ['#', 'Project', 'Publication', 'N/A', 'N/A']

        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        if len(relationships) > 15:
            print(f"\n{Fore.YELLOW}Showing 15 of {len(relationships)} relationships")

    def view_researcher_relationships(self):
        email = input(f"\n{Fore.WHITE}Enter researcher email: ").strip()
        if not email:
            print(f"{Fore.RED}ERROR: Email required")
            return

        researcher = mongodb.db.researchers.find_one({'email': email})
        if not researcher:
            print(f"{Fore.RED}ERROR: Researcher not found")
            return

        researcher_id = str(researcher['_id'])
        relationships = CollaborationService.get_researcher_relationships(researcher_id)

        if not relationships:
            print(f"\n{Fore.YELLOW}WARNING: No relationships found for this researcher")
            return

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.YELLOW}RELATIONSHIPS FOR: {researcher['name']} ({len(relationships)})")
        print(f"{Fore.CYAN}{'=' * 80}")

        table_data = []
        for i, rel in enumerate(relationships, 1):
            if rel['type'] in ['CO_AUTHORED_WITH', 'TEAMWORK_WITH'] and 'other_name' in rel:
                table_data.append([
                    i,
                    rel['type'],
                    rel['other_name'],
                    rel.get('collaboration_count', 1),
                    rel.get('last_collaboration', 'N/A')
                ])
            elif rel['type'] in ['SUPERVISES', 'PARTICIPATED_IN'] and 'project_title' in rel:
                table_data.append([
                    i,
                    rel['type'],
                    rel['project_title'],
                    rel.get('role', 'participant'),
                    'N/A'
                ])
            elif rel['type'] == 'AUTHORED' and 'publication_title' in rel:
                table_data.append([
                    i,
                    rel['type'],
                    rel['publication_title'],
                    rel.get('author_order', 1),
                    'N/A'
                ])

        headers = ['#', 'Type', 'With/Target', 'Count/Role', 'Last Collaboration']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def delete_relationship(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}DELETE RELATIONSHIP")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}Relationship Types:")
        print(f"{Fore.WHITE}[1] SUPERVISES")
        print(f"{Fore.WHITE}[2] PARTICIPATED_IN")
        print(f"{Fore.WHITE}[3] TEAMWORK_WITH")
        print(f"{Fore.WHITE}[4] AUTHORED")
        print(f"{Fore.WHITE}[5] CO_AUTHORED_WITH")
        print(f"{Fore.WHITE}[6] PRODUCED")

        choice = input(f"\n{Fore.YELLOW}Select relationship type to delete: ").strip()

        type_map = {
            '1': 'SUPERVISES',
            '2': 'PARTICIPATED_IN',
            '3': 'TEAMWORK_WITH',
            '4': 'AUTHORED',
            '5': 'CO_AUTHORED_WITH',
            '6': 'PRODUCED'
        }

        if choice not in type_map:
            print(f"{Fore.RED}ERROR: Invalid choice")
            return

        rel_type = type_map[choice]

        if rel_type in ['CO_AUTHORED_WITH', 'TEAMWORK_WITH']:
            email1 = input(f"{Fore.WHITE}Enter first researcher email: ").strip()
            email2 = input(f"{Fore.WHITE}Enter second researcher email: ").strip()

            researcher1 = mongodb.db.researchers.find_one({'email': email1})
            researcher2 = mongodb.db.researchers.find_one({'email': email2})

            if not researcher1 or not researcher2:
                print(f"{Fore.RED}ERROR: One or both researchers not found")
                return

            relationship_data = {
                'researcher1_id': str(researcher1['_id']),
                'researcher2_id': str(researcher2['_id'])
            }

        elif rel_type in ['SUPERVISES', 'PARTICIPATED_IN']:
            email = input(f"{Fore.WHITE}Enter researcher email: ").strip()
            project_title = input(f"{Fore.WHITE}Enter project title: ").strip()

            researcher = mongodb.db.researchers.find_one({'email': email})
            project = mongodb.db.projects.find_one({'title': project_title})

            if not researcher:
                print(f"{Fore.RED}ERROR: Researcher not found")
                return
            if not project:
                print(f"{Fore.RED}ERROR: Project not found")
                return

            relationship_data = {
                'researcher_id': str(researcher['_id']),
                'project_id': str(project['_id'])
            }

            if rel_type == 'SUPERVISES':
                relationship_data['supervisor_id'] = relationship_data['researcher_id']
                relationship_data['student_id'] = input(f"{Fore.WHITE}Enter student email: ").strip()
                student = mongodb.db.researchers.find_one({'email': relationship_data['student_id']})
                if not student:
                    print(f"{Fore.RED}ERROR: Student not found")
                    return
                relationship_data['student_id'] = str(student['_id'])

        elif rel_type == 'AUTHORED':
            email = input(f"{Fore.WHITE}Enter researcher email: ").strip()
            publication_title = input(f"{Fore.WHITE}Enter publication title: ").strip()

            researcher = mongodb.db.researchers.find_one({'email': email})
            publication = mongodb.db.publications.find_one({'title': publication_title})

            if not researcher:
                print(f"{Fore.RED}ERROR: Researcher not found")
                return
            if not publication:
                print(f"{Fore.RED}ERROR: Publication not found")
                return

            relationship_data = {
                'researcher_id': str(researcher['_id']),
                'publication_id': str(publication['_id'])
            }

        elif rel_type == 'PRODUCED':
            project_title = input(f"{Fore.WHITE}Enter project title: ").strip()
            publication_title = input(f"{Fore.WHITE}Enter publication title: ").strip()

            project = mongodb.db.projects.find_one({'title': project_title})
            publication = mongodb.db.publications.find_one({'title': publication_title})

            if not project:
                print(f"{Fore.RED}ERROR: Project not found")
                return
            if not publication:
                print(f"{Fore.RED}ERROR: Publication not found")
                return

            relationship_data = {
                'project_id': str(project['_id']),
                'publication_id': str(publication['_id'])
            }

        else:
            print(f"{Fore.RED}ERROR: Invalid relationship type")
            return

        print(f"\n{Fore.RED}WARNING: You are about to delete a {rel_type} relationship")
        confirm = input(f"{Fore.RED}Type 'DELETE' to confirm: ").strip()
        if confirm != 'DELETE':
            print(f"{Fore.YELLOW}Cancelled")
            return

        success, message = CollaborationService.delete_relationship(
            rel_type, relationship_data, self.current_user['id']
        )

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def run(self):
        if not self.login():
            return

        while True:
            try:
                self.display_menu()
                choice = input(f"\n{Fore.YELLOW}Select option: ")

                if choice == '0':
                    self.logout()
                    break
                elif choice == '1':
                    self.view_system_stats()
                elif choice == '2':
                    self.manage_researchers()
                elif choice == '3':
                    self.manage_projects()
                elif choice == '4':
                    self.manage_publications()
                elif choice == '5':
                    self.view_collaboration_analytics()
                elif choice == '6':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '7':
                    self.manage_all_relationships()
                else:
                    print(f"{Fore.RED}ERROR: Invalid choice")

                input(f"\n{Fore.CYAN}Press Enter to continue...")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}WARNING: Session interrupted")
                break
            except Exception as e:
                print(f"{Fore.RED}ERROR: {e}")

    def logout(self):
        if self.current_session:
            AuthService.logout(self.current_session)
            self.current_session = None
            self.current_user = None
            print(f"\n{Fore.GREEN}SUCCESS: Logged out successfully")


@click.command()
def main():
    cli = AdminCLI()
    cli.run()


if __name__ == "__main__":
    main()