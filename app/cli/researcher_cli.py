#!/usr/bin/env python3
"""
CLI Interface for Researchers
"""

import sys
import os
from pathlib import Path
from typing import Optional
from colorama import init, Fore, Style
import click
from tabulate import tabulate

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.auth_service import AuthService
from app.services.researcher_service import ResearcherService
from app.services.project_service import ProjectService
from app.services.publication_service import PublicationService
from app.services.collaboration_service import CollaborationService
from app.database.redis import redis_manager

init(autoreset=True)


class ResearcherCLI:
    """Researcher Command Line Interface"""

    def __init__(self):
        self.current_session = None
        self.current_user = None

    def get_password_input(self, prompt_text):
        """Get password input without click for Windows compatibility"""
        print(f"{prompt_text}: ", end='', flush=True)

        import msvcrt
        password_chars = []

        while True:
            char = msvcrt.getch()

            if char in [b'\r', b'\n']:  # Enter key
                print()
                break
            elif char == b'\x08':  # Backspace
                if password_chars:
                    password_chars.pop()
                    print('\b \b', end='', flush=True)
            elif char == b'\x03':  # Ctrl+C
                raise KeyboardInterrupt
            else:
                password_chars.append(char.decode('utf-8'))
                print('*', end='', flush=True)

        return ''.join(password_chars)

    def login(self):
        """Researcher login - Windows compatible version"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RESEARCHER LOGIN")
        print(f"{Fore.CYAN}{'=' * 50}")

        email = input(f"{Fore.WHITE}Email: ").strip()

        print(f"{Fore.WHITE}Password: ", end='', flush=True)
        password = self.get_password_input("")

        success, session_id, user_data, message = AuthService.login(email, password)

        if success:
            self.current_session = session_id
            self.current_user = user_data
            print(f"\n{Fore.GREEN}SUCCESS: {message}")
            print(f"{Fore.CYAN}Welcome, {user_data['name']}!")
            return True
        else:
            print(f"\n{Fore.RED}ERROR: {message}")
            return False

    def logout(self):
        """Logout"""
        if self.current_session:
            AuthService.logout(self.current_session)
            self.current_session = None
            self.current_user = None
            print(f"\n{Fore.GREEN}SUCCESS: Logged out successfully")
        else:
            print(f"{Fore.YELLOW}WARNING: Not logged in")

    def display_menu(self):
        """Display main menu"""
        menu = f"""
{Fore.CYAN}{'=' * 60}
{Fore.YELLOW}RESEARCHER DASHBOARD - {self.current_user['name'] if self.current_user else 'Guest'}
{Fore.CYAN}{'=' * 60}

{Fore.GREEN}[1]{Fore.WHITE} View My Profile
{Fore.GREEN}[2]{Fore.WHITE} Update Profile
{Fore.GREEN}[3]{Fore.WHITE} Search Researchers
{Fore.GREEN}[4]{Fore.WHITE} View Collaboration Network

{Fore.GREEN}[5]{Fore.WHITE} My Projects
{Fore.GREEN}[6]{Fore.WHITE} Create New Project
{Fore.GREEN}[7]{Fore.WHITE} Search Projects

{Fore.GREEN}[8]{Fore.WHITE} My Publications
{Fore.GREEN}[9]{Fore.WHITE} Add New Publication
{Fore.GREEN}[10]{Fore.WHITE} Search Publications

{Fore.GREEN}[11]{Fore.WHITE} View Collaborators
{Fore.GREEN}[12]{Fore.WHITE} Record Collaboration
{Fore.GREEN}[13]{Fore.WHITE} Suggested Collaborations

{Fore.GREEN}[0]{Fore.WHITE} Logout & Exit
{Fore.CYAN}{'=' * 60}
        """
        print(menu)

    def view_profile(self):
        """View profile"""
        if not self.current_user:
            print(f"{Fore.RED}ERROR: Please login first")
            return

        profile = ResearcherService.get_researcher_profile(self.current_user['user_id'])

        if not profile:
            print(f"{Fore.RED}ERROR: Profile not found")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}MY PROFILE")
        print(f"{Fore.CYAN}{'=' * 50}")

        basic_info = profile['basic_info']
        print(f"\n{Fore.GREEN}Basic Information:")
        print(f"{Fore.WHITE}   Name: {basic_info['name']}")
        print(f"   Email: {basic_info['email']}")
        print(f"   Department: {basic_info['department']}")
        print(f"   Status: {basic_info['profile_status']}")
        print(f"   Interests: {', '.join(basic_info['research_interests'])}")

        stats = profile['statistics']
        print(f"\n{Fore.GREEN}Statistics:")
        print(f"{Fore.WHITE}   Projects: {stats['projects_count']}")
        print(f"   Publications: {stats['publications_count']}")
        print(f"   Collaborators: {stats['collaborators_count']}")
        print(f"   Activity Score: {profile['activity_score']}")

        if profile['collaborators']:
            print(f"\n{Fore.GREEN}Top Collaborators:")
            table_data = []
            for i, collab in enumerate(profile['collaborators'][:5], 1):
                table_data.append([
                    i,
                    collab['collaborator_name'],
                    collab['department'],
                    collab['collaboration_count'],
                    ', '.join(collab['collaboration_types'][:2])
                ])

            headers = ['#', 'Name', 'Department', 'Collaborations', 'Types']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def run(self):
        """Run interactive interface"""
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
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '3':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '4':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '5':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '6':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '7':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '8':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '9':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '10':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '11':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '12':
                    print(f"{Fore.YELLOW}Coming soon...")
                elif choice == '13':
                    print(f"{Fore.YELLOW}Coming soon...")
                else:
                    print(f"{Fore.RED}ERROR: Invalid choice")

                input(f"\n{Fore.CYAN}Press Enter to continue...")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}WARNING: Session interrupted")
                break
            except Exception as e:
                print(f"{Fore.RED}ERROR: {e}")


@click.command()
def main():
    """Research Collaboration System - Researcher Interface"""
    cli = ResearcherCLI()
    cli.run()


if __name__ == "__main__":
    main()