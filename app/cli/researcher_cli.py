#!/usr/bin/env python3
"""
CLI Interface for Researchers
"""

import sys
from pathlib import Path
from colorama import init, Fore, Style
import click
from tabulate import tabulate

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.auth_service import AuthService
from app.services.researcher_service import ResearcherService
from app.services.project_service import ProjectService
from app.services.publication_service import PublicationService
from app.services.collaboration_service import CollaborationService
from app.database.mongodb import mongodb
from app.database.redis import redis_manager

init(autoreset=True)


class ResearcherCLI:
    def __init__(self):
        self.current_session = None
        self.current_user = None

    def get_password_input(self, prompt_text):
        print(f"{prompt_text}: ", end='', flush=True)

        if sys.platform == "win32":
            import msvcrt
            password_chars = []
            while True:
                char = msvcrt.getch()
                if char in [b'\r', b'\n']:
                    print()
                    break
                elif char == b'\x08':
                    if password_chars:
                        password_chars.pop()
                        print('\b \b', end='', flush=True)
                elif char == b'\x03':
                    raise KeyboardInterrupt
                else:
                    password_chars.append(char.decode('utf-8'))
                    print('*', end='', flush=True)
            return ''.join(password_chars)
        else:
            import getpass
            return getpass.getpass("")

    def login(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RESEARCHER LOGIN")
        print(f"{Fore.CYAN}{'=' * 50}")

        email = input(f"{Fore.WHITE}Email: ").strip()
        password = self.get_password_input(f"{Fore.WHITE}Password")

        success, session_id, user_data, message = AuthService.login(email, password)

        if success:
            if user_data.get('profile_status') != 'approved':
                print(f"\n{Fore.YELLOW}WARNING: Your account is {user_data.get('profile_status')}")
                print(f"{Fore.WHITE}Please contact administrator for approval")
                return False

            self.current_session = session_id
            self.current_user = user_data
            print(f"\n{Fore.GREEN}SUCCESS: {message}")
            print(f"{Fore.CYAN}Welcome, {user_data['name']}!")
            return True
        else:
            print(f"\n{Fore.RED}ERROR: {message}")
            return False

    def display_menu(self):
        menu = f"""
{Fore.CYAN}{'=' * 60}
{Fore.YELLOW}RESEARCHER DASHBOARD - {self.current_user['name'] if self.current_user else 'Guest'}
{Fore.CYAN}{'=' * 60}

{Fore.GREEN}[1]{Fore.WHITE} My Profile & Statistics
{Fore.GREEN}[2]{Fore.WHITE} Update My Profile
{Fore.GREEN}[3]{Fore.WHITE} Search Researchers

{Fore.GREEN}[4]{Fore.WHITE} My Projects
{Fore.GREEN}[5]{Fore.WHITE} Create New Project
{Fore.GREEN}[6]{Fore.WHITE} Search Projects

{Fore.GREEN}[7]{Fore.WHITE} My Publications
{Fore.GREEN}[8]{Fore.WHITE} Add New Publication
{Fore.GREEN}[9]{Fore.WHITE} Search Publications

{Fore.GREEN}[10]{Fore.WHITE} My Collaborations
{Fore.GREEN}[11]{Fore.WHITE} Collaboration Network
{Fore.GREEN}[12]{Fore.WHITE} Suggested Collaborators

{Fore.GREEN}[0]{Fore.WHITE} Logout & Exit
{Fore.CYAN}{'=' * 60}
        """
        print(menu)

    def view_profile(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        researcher_id = self.current_user['id']
        details = ResearcherService.get_researcher_details(researcher_id)

        if not details:
            print(f"{Fore.RED}ERROR: Could not get profile details")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}MY PROFILE")
        print(f"{Fore.CYAN}{'=' * 50}")

        basic_info = details.get('researcher_info', {})
        print(f"\n{Fore.GREEN}Basic Information:")
        print(f"{Fore.WHITE}   Name: {basic_info.get('name', 'N/A')}")
        print(f"   Email: {basic_info.get('email', 'N/A')}")
        print(f"   Department: {basic_info.get('department', 'N/A')}")
        print(f"   Status: {basic_info.get('profile_status', 'N/A')}")
        print(f"   Role: {basic_info.get('role', 'researcher')}")

        interests = basic_info.get('research_interests', [])
        if interests:
            print(f"   Research Interests: {', '.join(interests)}")

        print(f"\n{Fore.GREEN}Statistics:")
        print(f"{Fore.WHITE}   Projects: {details.get('projects_count', 0)}")
        print(f"   Publications: {details.get('publications_count', 0)}")
        print(f"   Collaborators: {details.get('collaborators_count', 0)}")
        print(f"   Teamwork Partners: {details.get('teamwork_count', 0)}")
        print(f"   Supervised Projects: {len(details.get('supervised_projects', []))}")

        stats = ResearcherService.get_researcher_statistics(researcher_id)
        if stats:
            print(f"\n{Fore.GREEN}Advanced Statistics:")
            print(f"{Fore.WHITE}   First Author Publications: {stats.get('first_author_count', 0)}")
            print(f"   Total Co-authors: {stats.get('coauthors_count', 0)}")
            print(f"   Total Team Members: {stats.get('teammates_count', 0)}")
            print(f"   Average Collaborations: {stats.get('average_collaborations_per_researcher', 0):.1f}")

        top_collaborators = ResearcherService.get_top_collaborators(researcher_id, 5)
        if top_collaborators:
            print(f"\n{Fore.GREEN}Top Collaborators:")
            table_data = []
            for i, collab in enumerate(top_collaborators, 1):
                table_data.append([
                    i,
                    collab['name'],
                    collab['department'],
                    collab['collaboration_count'],
                    collab['publications_together']
                ])
            headers = ['#', 'Name', 'Department', 'Collaborations', 'Publications']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def update_profile(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}UPDATE PROFILE")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.YELLOW}Leave field empty to keep current value:")

        name = input(f"{Fore.WHITE}Name [{self.current_user['name']}]: ").strip()
        department = input(f"{Fore.WHITE}Department [{self.current_user.get('department', '')}]: ").strip()
        interests_input = input(f"{Fore.WHITE}Research Interests (comma-separated): ").strip()

        update_data = {}
        if name:
            update_data['name'] = name
        if department:
            update_data['department'] = department
        if interests_input:
            update_data['research_interests'] = [interest.strip() for interest in interests_input.split(',')]

        if not update_data:
            print(f"{Fore.YELLOW}No changes made")
            return

        success, message = ResearcherService.update_researcher_profile(
            self.current_user['id'], update_data
        )

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
            if 'name' in update_data:
                self.current_user['name'] = update_data['name']
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def search_researchers(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}SEARCH RESEARCHERS")
        print(f"{Fore.CYAN}{'=' * 50}")

        query = input(f"{Fore.WHITE}Search (name, email, department, interests): ").strip()

        print(f"\n{Fore.YELLOW}Filters:")
        department = input(f"{Fore.WHITE}Department (optional): ").strip()
        interests = input(f"{Fore.WHITE}Research Interest (optional): ").strip()

        filters = {}
        if department:
            filters['department'] = department
        if interests:
            filters['research_interests'] = interests

        researchers = ResearcherService.search_researchers(query, filters, 20)

        if not researchers:
            print(f"\n{Fore.YELLOW}No researchers found")
            return

        print(f"\n{Fore.GREEN}Found {len(researchers)} researcher(s):")

        table_data = []
        for i, researcher in enumerate(researchers, 1):
            stats = researcher.get('stats', {})
            table_data.append([
                i,
                researcher['name'],
                researcher['email'],
                researcher['department'],
                researcher['profile_status'],
                stats.get('projects_count', 0),
                stats.get('publications_count', 0)
            ])

        headers = ['#', 'Name', 'Email', 'Department', 'Status', 'Projects', 'Publications']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        print(f"\n{Fore.GREEN}[V]#{Fore.WHITE} View details")
        print(f"{Fore.GREEN}[S]{Fore.WHITE} Search again")
        print(f"{Fore.GREEN}[R]{Fore.WHITE} Return")

        choice = input(f"\n{Fore.YELLOW}Select option: ").upper()

        if choice.startswith('V') and choice[1:].isdigit():
            idx = int(choice[1:]) - 1
            if 0 <= idx < len(researchers):
                self.view_researcher_details(researchers[idx]['_id'])

    def view_researcher_details(self, researcher_id):
        details = ResearcherService.get_researcher_details(researcher_id)

        if not details:
            print(f"{Fore.RED}ERROR: Could not get researcher details")
            return

        basic_info = details.get('researcher_info', {})
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RESEARCHER DETAILS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}Basic Information:")
        print(f"{Fore.WHITE}   Name: {basic_info.get('name', 'N/A')}")
        print(f"   Email: {basic_info.get('email', 'N/A')}")
        print(f"   Department: {basic_info.get('department', 'N/A')}")
        print(f"   Status: {basic_info.get('profile_status', 'N/A')}")

        interests = basic_info.get('research_interests', [])
        if interests:
            print(f"   Research Interests: {', '.join(interests)}")

        print(f"\n{Fore.GREEN}Statistics:")
        print(f"{Fore.WHITE}   Projects: {details.get('projects_count', 0)}")
        print(f"   Publications: {details.get('publications_count', 0)}")
        print(f"   Collaborators: {details.get('collaborators_count', 0)}")

        if details.get('collaborations'):
            print(f"\n{Fore.GREEN}Top Collaborators:")
            for i, collab in enumerate(details['collaborations'][:5], 1):
                print(f"{Fore.WHITE}   {i}. {collab['name']} - {collab['collaboration_count']} collaborations")

    def my_projects(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        researcher_id = self.current_user['id']
        projects = ProjectService.get_projects_by_researcher(researcher_id)

        if not projects:
            print(f"\n{Fore.YELLOW}You are not involved in any projects")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}MY PROJECTS ({len(projects)})")
        print(f"{Fore.CYAN}{'=' * 50}")

        table_data = []
        for i, project in enumerate(projects, 1):
            table_data.append([
                i,
                project.get('title', 'N/A')[:40],
                project.get('status', 'N/A'),
                project.get('user_role', 'participant'),
                len(project.get('participants', [])),
                project.get('created_at').strftime('%Y-%m-%d') if hasattr(project.get('created_at'),
                                                                          'strftime') else 'N/A'
            ])

        headers = ['#', 'Title', 'Status', 'Role', 'Participants', 'Created']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        print(f"\n{Fore.GREEN}[V]#{Fore.WHITE} View project details")
        print(f"{Fore.GREEN}[C]{Fore.WHITE} Create new project")
        print(f"{Fore.GREEN}[R]{Fore.WHITE} Return")

        choice = input(f"\n{Fore.YELLOW}Select option: ").upper()

        if choice.startswith('V') and choice[1:].isdigit():
            idx = int(choice[1:]) - 1
            if 0 <= idx < len(projects):
                self.view_project_details(str(projects[idx]['_id']))
        elif choice == 'C':
            self.create_project()

    def create_project(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}CREATE NEW PROJECT")
        print(f"{Fore.CYAN}{'=' * 50}")

        title = input(f"{Fore.WHITE}Project Title: ").strip()
        if not title:
            print(f"{Fore.RED}ERROR: Title is required")
            return

        description = input(f"{Fore.WHITE}Description: ").strip()
        if not description:
            print(f"{Fore.RED}ERROR: Description is required")
            return

        research_area = input(f"{Fore.WHITE}Research Area: ").strip()
        start_date = input(f"{Fore.WHITE}Start Date (YYYY-MM-DD) [today]: ").strip()
        end_date = input(f"{Fore.WHITE}End Date (YYYY-MM-DD) [optional]: ").strip()

        project_data = {
            'title': title,
            'description': description,
            'research_area': research_area,
            'start_date': start_date if start_date else None,
            'end_date': end_date if end_date else None
        }

        success, project_id, message = ProjectService.create_project(
            self.current_user['id'], project_data
        )

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
            print(f"{Fore.CYAN}Project ID: {project_id}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def view_project_details(self, project_id):
        details = ProjectService.get_project_details(project_id)

        if not details:
            print(f"{Fore.RED}ERROR: Could not get project details")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}PROJECT DETAILS")
        print(f"{Fore.CYAN}{'=' * 50}")

        project_info = details.get('project_info', {})
        print(f"\n{Fore.GREEN}Project Information:")
        print(f"{Fore.WHITE}   Title: {project_info.get('title', 'N/A')}")
        print(f"   Creator: {project_info.get('creator_name', 'N/A')}")
        print(f"   Status: {project_info.get('status', 'N/A')}")
        print(f"   Research Area: {project_info.get('research_area', 'N/A')}")
        print(f"   Start Date: {project_info.get('start_date', 'N/A')}")
        print(f"   End Date: {project_info.get('end_date', 'N/A')}")

        print(f"\n{Fore.GREEN}Statistics:")
        print(f"{Fore.WHITE}   Participants: {details.get('participants_count', 0)}")
        print(f"   Publications: {details.get('publications_count', 0)}")

        if details.get('supervisor'):
            print(f"   Supervisor: {details['supervisor'].get('name', 'N/A')}")

        if details.get('participants'):
            print(f"\n{Fore.GREEN}Participants:")
            for participant in details['participants'][:10]:
                print(f"{Fore.WHITE}   - {participant.get('name', 'N/A')} ({participant.get('role', 'participant')})")

    def search_projects(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}SEARCH PROJECTS")
        print(f"{Fore.CYAN}{'=' * 50}")

        query = input(f"{Fore.WHITE}Search (title, description, research area): ").strip()

        print(f"\n{Fore.YELLOW}Filters:")
        status = input(f"{Fore.WHITE}Status (active/completed/pending) [optional]: ").strip()
        research_area = input(f"{Fore.WHITE}Research Area [optional]: ").strip()

        filters = {}
        if status and status in ['active', 'completed', 'pending']:
            filters['status'] = status
        if research_area:
            filters['research_area'] = research_area

        projects = ProjectService.search_projects(query, filters, 20)

        if not projects:
            print(f"\n{Fore.YELLOW}No projects found")
            return

        print(f"\n{Fore.GREEN}Found {len(projects)} project(s):")

        table_data = []
        for i, project in enumerate(projects, 1):
            table_data.append([
                i,
                project.get('title', 'N/A')[:40],
                project.get('creator_name', 'N/A')[:20],
                project.get('status', 'N/A'),
                len(project.get('participants', [])),
                project.get('publication_count', 0)
            ])

        headers = ['#', 'Title', 'Creator', 'Status', 'Participants', 'Publications']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def my_publications(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        researcher_id = self.current_user['id']
        publications = PublicationService.get_publications_by_researcher(researcher_id)

        if not publications:
            print(f"\n{Fore.YELLOW}You have no publications")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}MY PUBLICATIONS ({len(publications)})")
        print(f"{Fore.CYAN}{'=' * 50}")

        table_data = []
        for i, pub in enumerate(publications, 1):
            table_data.append([
                i,
                pub.get('title', 'N/A')[:50],
                pub.get('year', 'N/A'),
                pub.get('journal', 'N/A')[:20],
                pub.get('author_role', 'co_author'),
                pub.get('citation_count', 0)
            ])

        headers = ['#', 'Title', 'Year', 'Journal', 'Role', 'Citations']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def create_publication(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ADD NEW PUBLICATION")
        print(f"{Fore.CYAN}{'=' * 50}")

        title = input(f"{Fore.WHITE}Title: ").strip()
        if not title:
            print(f"{Fore.RED}ERROR: Title is required")
            return

        year = input(f"{Fore.WHITE}Year: ").strip()
        if not year or not year.isdigit():
            print(f"{Fore.RED}ERROR: Valid year is required")
            return

        journal = input(f"{Fore.WHITE}Journal: ").strip()
        abstract = input(f"{Fore.WHITE}Abstract: ").strip()
        keywords_input = input(f"{Fore.WHITE}Keywords (comma-separated): ").strip()

        authors = []
        print(f"\n{Fore.YELLOW}Add Authors (starting with yourself):")
        print(f"{Fore.WHITE}Yourself added automatically as first author")

        add_more = input(f"{Fore.WHITE}Add more authors? (yes/no): ").strip().lower()
        while add_more in ['yes', 'y']:
            author_email = input(f"{Fore.WHITE}Author email: ").strip()
            if author_email:
                researcher = mongodb.db.researchers.find_one({'email': author_email})
                if researcher:
                    authors.append({
                        'researcher_id': str(researcher['_id']),
                        'name': researcher['name'],
                        'order': len(authors) + 2
                    })
                    print(f"{Fore.GREEN}Added: {researcher['name']}")
                else:
                    print(f"{Fore.RED}Researcher not found")
            add_more = input(f"{Fore.WHITE}Add another author? (yes/no): ").strip().lower()

        publication_data = {
            'title': title,
            'year': int(year),
            'journal': journal,
            'abstract': abstract,
            'keywords': [k.strip() for k in keywords_input.split(',')] if keywords_input else [],
            'authors': authors
        }

        success, publication_id, message = PublicationService.create_publication(
            self.current_user['id'], publication_data
        )

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
            print(f"{Fore.CYAN}Publication ID: {publication_id}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def my_collaborations(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        researcher_id = self.current_user['id']
        relationships = CollaborationService.get_researcher_relationships(researcher_id)

        if not relationships:
            print(f"\n{Fore.YELLOW}No collaboration data found")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}MY COLLABORATIONS ({len(relationships)})")
        print(f"{Fore.CYAN}{'=' * 50}")

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

        headers = ['#', 'Type', 'With/Target', 'Count/Role', 'Last Collaboration']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def collaboration_network(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        researcher_id = self.current_user['id']

        try:
            depth_input = input(f"{Fore.WHITE}Network depth (1-3) [2]: ").strip()
            depth = int(depth_input) if depth_input.isdigit() and 1 <= int(depth_input) <= 3 else 2

            network = ResearcherService.get_collaboration_network(researcher_id, depth)

            if not network or 'nodes' not in network:
                print(f"{Fore.YELLOW}No network data found")
                return

            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}COLLABORATION NETWORK (Depth: {depth})")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}Network Statistics:")
            print(f"{Fore.WHITE}   Total Nodes: {network.get('total_nodes', 0)}")
            print(f"   Total Connections: {network.get('total_edges', 0)}")
            print(f"   Central Researcher: {network.get('central_researcher', {}).get('name', 'You')}")

            if network.get('nodes'):
                print(f"\n{Fore.GREEN}Connected Researchers:")
                for i, node in enumerate(network['nodes'][:10], 1):
                    if node['id'] != researcher_id:
                        print(f"{Fore.WHITE}   {i}. {node['label']}")

        except Exception as e:
            print(f"{Fore.RED}ERROR: Could not generate network: {e}")

    def suggested_collaborators(self):
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        researcher_id = self.current_user['id']
        suggestions = ResearcherService.suggest_collaborators(researcher_id, 10)

        if not suggestions:
            print(f"\n{Fore.YELLOW}No suggestions available")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}SUGGESTED COLLABORATORS")
        print(f"{Fore.CYAN}{'=' * 50}")

        table_data = []
        for i, suggestion in enumerate(suggestions, 1):
            table_data.append([
                i,
                suggestion['name'],
                suggestion.get('common_interests_count', 0),
                'Yes' if suggestion.get('has_collaborated') else 'No',
                suggestion.get('collaboration_count', 0)
            ])

        headers = ['#', 'Name', 'Common Interests', 'Collaborated Before', 'Collaborations']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def run(self):
        if not self.login():
            return

        while True:
            try:
                self.display_menu()
                choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

                if choice == '0':
                    self.logout()
                    break
                elif choice == '1':
                    self.view_profile()
                elif choice == '2':
                    self.update_profile()
                elif choice == '3':
                    self.search_researchers()
                elif choice == '4':
                    self.my_projects()
                elif choice == '5':
                    self.create_project()
                elif choice == '6':
                    self.search_projects()
                elif choice == '7':
                    self.my_publications()
                elif choice == '8':
                    self.create_publication()
                elif choice == '9':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '10':
                    self.my_collaborations()
                elif choice == '11':
                    self.collaboration_network()
                elif choice == '12':
                    self.suggested_collaborators()
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
    cli = ResearcherCLI()
    cli.run()


if __name__ == "__main__":
    main()