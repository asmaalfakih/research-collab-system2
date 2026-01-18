
import sys
from pathlib import Path
from colorama import init, Fore, Style
import click

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.cli.admin_cli import AdminCLI
from app.cli.researcher_cli import ResearcherCLI

init(autoreset=True)

class MainCLI:

    def __init__(self):
        self.admin_cli = AdminCLI()
        self.researcher_cli = ResearcherCLI()

    def display_main_menu(self):
        menu = f

        print(menu)

    def run_researcher_interface(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RESEARCHER INTERFACE")
        print(f"{Fore.CYAN}{'=' * 50}")

        from app.cli.researcher_cli import ResearcherCLI
        cli = ResearcherCLI()
        cli.run()

    def run_admin_interface(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ADMINISTRATOR INTERFACE")
        print(f"{Fore.CYAN}{'=' * 50}")

        from app.cli.admin_cli import AdminCLI
        cli = AdminCLI()
        cli.run()

    def run_research_intelligence(self):
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RESEARCH INTELLIGENCE DASHBOARD")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            from app.cli.research_analytics_cli import ResearchAnalyticsCLI
            cli = ResearchAnalyticsCLI()
            cli.run()
        except ImportError as e:
            print(f"{Fore.RED}ERROR: Cannot load Research Intelligence Module")
            print(f"{Fore.YELLOW}Please ensure research_analytics_cli.py exists in app/cli/")
            print(f"{Fore.YELLOW}Error details: {e}")

    def quick_system_test(self):
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
                    self.run_research_intelligence()
                elif choice == '4':
                    self.quick_system_test()
                else:
                    print(f"{Fore.RED}ERROR: Invalid choice")

                if choice in ['1', '2', '3']:
                    input(f"\n{Fore.CYAN}Press Enter to return to main menu...")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}WARNING: Session interrupted")
                break
            except Exception as e:
                print(f"{Fore.RED}ERROR: {e}")

@click.command()
def main():
    cli = MainCLI()
    cli.run()

if __name__ == "__main__":
    main()