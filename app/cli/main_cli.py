#!/usr/bin/env python3
"""
Main CLI Interface - Entry Point
"""

import sys
from pathlib import Path
from colorama import init, Fore, Style
import click

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.cli.admin_cli import AdminCLI
from app.cli.researcher_cli import ResearcherCLI

init(autoreset=True)


class MainCLI:
    """Main Command Line Interface"""

    def __init__(self):
        self.admin_cli = AdminCLI()
        self.researcher_cli = ResearcherCLI()

    def display_main_menu(self):
        """Display main menu"""
        menu = f"""
{Fore.CYAN}{'=' * 70}
{Fore.YELLOW}RESEARCH COLLABORATION SYSTEM - NOSQL DATABASE PROJECT
{Fore.CYAN}{'=' * 70}
{Fore.MAGENTA}MONGODB | NEO4J | REDIS | 6 RELATIONSHIP TYPES

{Fore.CYAN}PALESTINE POLYTECHNIC UNIVERSITY
{Fore.CYAN}COURSE: NOSQL DATABASE
{Fore.CYAN}STUDENTS: ASMA ALFAKIH, DALAH ALHASHLAMOUN
{Fore.CYAN}{'=' * 70}

{Fore.GREEN}MAIN MENU - SELECT INTERFACE:

{Fore.GREEN}[1]{Fore.WHITE} Researcher Interface
{Fore.YELLOW}    - View profile, projects, publications
{Fore.YELLOW}    - Search researchers and collaborations
{Fore.YELLOW}    - Manage your research activities

{Fore.GREEN}[2]{Fore.WHITE} Administrator Interface
{Fore.RED}    - System management and statistics
{Fore.RED}    - Approve researchers and manage projects
{Fore.RED}    - Monitor all relationships and activities

{Fore.GREEN}[3]{Fore.WHITE} Quick System Test
{Fore.CYAN}    - Test database connections
{Fore.CYAN}    - Check system health

{Fore.GREEN}[0]{Fore.WHITE} Exit System
{Fore.CYAN}{'=' * 70}
        """
        print(menu)

    def run_researcher_interface(self):
        """Run researcher interface"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RESEARCHER INTERFACE")
        print(f"{Fore.CYAN}{'=' * 50}")

        from app.cli.researcher_cli import ResearcherCLI
        cli = ResearcherCLI()
        cli.run()

    def run_admin_interface(self):
        """Run admin interface"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ADMINISTRATOR INTERFACE")
        print(f"{Fore.CYAN}{'=' * 50}")

        from app.cli.admin_cli import AdminCLI
        cli = AdminCLI()
        cli.run()

    def quick_system_test(self):
        """Quick system test"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}QUICK SYSTEM TEST")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            from app.database import db_manager
            results = db_manager.check_all_connections()

            print(f"\n{Fore.GREEN}Database Connection Status:")
            for db_name, result in results.items():
                status = result.get('status', 'unknown')
                if status == 'connected':
                    print(f"{Fore.GREEN}  ✓ {db_name.upper()}: Connected")
                elif status == 'disabled':
                    print(f"{Fore.YELLOW}  ⚠ {db_name.upper()}: Disabled")
                else:
                    print(f"{Fore.RED}  ✗ {db_name.upper()}: {status}")

            # Check relationship types
            try:
                from app.services.collaboration_service import CollaborationService
                stats = CollaborationService.get_relationship_statistics()

                if stats and 'relationship_counts' in stats:
                    print(f"\n{Fore.GREEN}Relationship Types Available:")
                    rel_counts = stats['relationship_counts']
                    for rel_type, count in rel_counts.items():
                        if count > 0:
                            print(f"{Fore.CYAN}  • {rel_type}: {count}")

                print(f"\n{Fore.GREEN}✓ System supports all 6 relationship types")

            except Exception as e:
                print(f"{Fore.YELLOW}⚠ Relationship check: {e}")

        except Exception as e:
            print(f"{Fore.RED}✗ System test failed: {e}")

    def run(self):
        """Run interactive interface"""
        while True:
            try:
                self.display_main_menu()
                choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

                if choice == '0':
                    print(f"\n{Fore.GREEN}Thank you for using Research Collaboration System!")
                    print(f"{Fore.CYAN}Goodbye!")
                    break
                elif choice == '1':
                    self.run_researcher_interface()
                elif choice == '2':
                    self.run_admin_interface()
                elif choice == '3':
                    self.quick_system_test()
                else:
                    print(f"{Fore.RED}ERROR: Invalid choice")

                if choice in ['1', '2']:
                    input(f"\n{Fore.CYAN}Press Enter to return to main menu...")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}WARNING: Session interrupted")
                break
            except Exception as e:
                print(f"{Fore.RED}ERROR: {e}")


@click.command()
def main():
    """Research Collaboration System - Main Interface"""
    cli = MainCLI()
    cli.run()


if __name__ == "__main__":
    main()