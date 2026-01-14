#!/usr/bin/env python3
"""
CLI Interface for Administrators
"""

import sys
from pathlib import Path
from colorama import init, Fore, Style
import click
from tabulate import tabulate

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.auth_service import AuthService
from app.services.researcher_service import ResearcherService
from app.services.collaboration_service import CollaborationService
from app.database.mongodb import mongodb
from app.database.redis import redis_manager

init(autoreset=True)


class AdminCLI:
    """Administrator Command Line Interface"""

    def __init__(self):
        self.current_session = None
        self.current_user = None

    def login(self):
        """Admin login (modified auto-login version)"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ADMIN LOGIN - AUTO LOGIN")
        print(f"{Fore.CYAN}{'=' * 50}")

        # Use default credentials to bypass input issues
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

            # Create admin if doesn't exist
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
                # Create in Neo4j
                neo4j.create_researcher_node({
                    'id': admin_id,
                    'name': admin_data['name'],
                    'email': admin_data['email'],
                    'department': admin_data['department'],
                    'profile_status': admin_data['profile_status']
                })

                print(f"{Fore.GREEN}SUCCESS: Admin account created!")

                # Try login again
                success, session_id, user_data, message = AuthService.login(email, password)
                if success:
                    self.current_session = session_id
                    self.current_user = user_data
                    print(f"\n{Fore.GREEN}SUCCESS: Auto-login successful!")
                    return True

            return False

    def display_menu(self):
        """Display admin menu"""
        menu = f"""
{Fore.CYAN}{'=' * 60}
{Fore.YELLOW}ADMIN DASHBOARD - {self.current_user['name'] if self.current_user else 'System'}
{Fore.CYAN}{'=' * 60}

{Fore.GREEN}[1]{Fore.WHITE} View System Statistics
{Fore.GREEN}[2]{Fore.WHITE} Manage Researchers
{Fore.GREEN}[3]{Fore.WHITE} View Collaboration Analytics
{Fore.GREEN}[4]{Fore.WHITE} Monitor System Activity

{Fore.GREEN}[0]{Fore.WHITE} Logout & Exit
{Fore.CYAN}{'=' * 60}
        """
        print(menu)

    def view_system_stats(self):
        """Display system statistics"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}SYSTEM STATISTICS")
        print(f"{Fore.CYAN}{'=' * 50}")

        # MongoDB Statistics
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

        # Redis Statistics
        print(f"\n{Fore.GREEN}REDIS CACHE:")
        redis_stats = redis_manager.get_system_stats()
        if redis_stats.get('status') == 'connected':
            print(f"{Fore.WHITE}   Status: Connected")
            print(f"   Memory Used: {redis_stats.get('memory', {}).get('used', 'N/A')}")
            print(f"   Connected Clients: {redis_stats.get('clients', {}).get('connected', 0)}")
            print(f"   Cache Hit Rate: {redis_manager.get_cache_hit_rate():.2%}")
        else:
            print(f"{Fore.RED}   Status: {redis_stats.get('status', 'Disconnected')}")

        # Collaboration Statistics
        print(f"\n{Fore.GREEN}COLLABORATION NETWORK:")
        collab_stats = CollaborationService.get_collaboration_network_stats()

        if collab_stats:
            print(f"{Fore.WHITE}   Total Researchers: {collab_stats.get('total_researchers', 'N/A')}")
            print(f"   Total Collaborations: {collab_stats.get('total_collaborations', 'N/A')}")
            print(f"   Average Collaborations: {collab_stats.get('average_collaborations', 0):.1f}")
            print(f"   Network Density: {collab_stats.get('collaboration_density', 0):.3f}")

    def manage_researchers(self):
        """Manage researchers"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}MANAGE RESEARCHERS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}[1]{Fore.WHITE} View All Researchers")
        print(f"{Fore.GREEN}[2]{Fore.WHITE} View Pending Approvals")
        print(f"{Fore.GREEN}[3]{Fore.WHITE} Back to Main Menu")

        choice = input(f"\n{Fore.YELLOW}Select option: ")

        if choice == '1':
            self.view_all_researchers()
        elif choice == '2':
            self.view_pending_approvals()
        elif choice == '3':
            return
        else:
            print(f"{Fore.RED}ERROR: Invalid choice")

    def view_all_researchers(self):
        """View all researchers"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ALL RESEARCHERS")
        print(f"{Fore.CYAN}{'=' * 50}")

        top_researchers = ResearcherService.get_top_researchers(20)

        if not top_researchers:
            print(f"\n{Fore.YELLOW}WARNING: No researchers found")
            return

        table_data = []
        for i, researcher in enumerate(top_researchers, 1):
            table_data.append([
                i,
                researcher['name'],
                researcher['email'],
                researcher['department'],
                researcher['profile_status'],
                researcher['publications_count'],
                researcher['projects_count'],
                researcher['total_score']
            ])

        headers = ['#', 'Name', 'Email', 'Department', 'Status', 'Pubs', 'Projs', 'Score']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def view_pending_approvals(self):
        """View pending researcher approvals"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}PENDING APPROVALS")
        print(f"{Fore.CYAN}{'=' * 50}")

        pending_researchers = mongodb.get_pending_researchers()

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

    def run(self):
        """Run interactive interface"""
        # Auto login
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
                    self.view_collaboration_analytics()
                elif choice == '4':
                    print(f"{Fore.YELLOW}WARNING: Coming soon...")
                else:
                    print(f"{Fore.RED}ERROR: Invalid choice")

                input(f"\n{Fore.CYAN}Press Enter to continue...")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}WARNING: Session interrupted")
                break
            except Exception as e:
                print(f"{Fore.RED}ERROR: {e}")

    def view_collaboration_analytics(self):
        """View collaboration analytics"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}COLLABORATION ANALYTICS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}[1]{Fore.WHITE} Most Collaborative Pairs")
        print(f"{Fore.GREEN}[2]{Fore.WHITE} Network Statistics")
        print(f"{Fore.GREEN}[3]{Fore.WHITE} Back to Main Menu")

        choice = input(f"\n{Fore.YELLOW}Select option: ")

        if choice == '1':
            self.view_most_collaborative_pairs()
        elif choice == '2':
            self.view_network_statistics()
        elif choice == '3':
            return
        else:
            print(f"{Fore.RED}ERROR: Invalid choice")

    def view_most_collaborative_pairs(self):
        """View most collaborative pairs"""
        print(f"\n{Fore.WHITE}Number of pairs to show (default: 10): ")
        try:
            limit = int(input())
        except:
            limit = 10

        pairs = CollaborationService.get_most_collaborative_pairs(limit)

        if not pairs:
            print(f"\n{Fore.YELLOW}WARNING: No collaboration data found")
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
                ', '.join(pair['collaboration_types'][:3]) if pair['collaboration_types'] else 'N/A'
            ])

        headers = ['#', 'Researcher 1', 'Researcher 2', 'Count', 'Types']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def view_network_statistics(self):
        """View network statistics"""
        stats = CollaborationService.get_collaboration_network_stats()

        if not stats:
            print(f"\n{Fore.YELLOW}WARNING: No network statistics available")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}NETWORK STATISTICS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}Basic Statistics:")
        print(f"{Fore.WHITE}   Total Researchers: {stats.get('total_researchers', 'N/A')}")
        print(f"   Total Collaborations: {stats.get('total_collaborations', 'N/A')}")
        print(f"   Average Collaborations: {stats.get('average_collaborations', 0):.1f}")

        print(f"\n{Fore.GREEN}Advanced Metrics:")
        print(f"{Fore.WHITE}   Network Density: {stats.get('collaboration_density', 0):.3f}")

    def logout(self):
        """Logout"""
        if self.current_session:
            AuthService.logout(self.current_session)
            self.current_session = None
            self.current_user = None
            print(f"\n{Fore.GREEN}SUCCESS: Logged out successfully")


@click.command()
def main():
    """Research Collaboration System - Admin Interface"""
    cli = AdminCLI()
    cli.run()


if __name__ == "__main__":
    main()