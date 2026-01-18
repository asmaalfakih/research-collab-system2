"""
CLI Interface for Research Analytics
"""

import sys
from pathlib import Path
import click
from tabulate import tabulate

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.research_intelligence_service import ResearchIntelligenceService
from app.database.mongodb import mongodb


class ResearchAnalyticsCLI:
    """Command Line Interface for Research Intelligence"""

    def __init__(self):
        self.current_researcher = None

    def display_main_menu(self):
        menu = """
========================================
RESEARCH INTELLIGENCE DASHBOARD
========================================

[1] Find Research Bridge Between Researchers
[2] Find Hidden Experts in a Field
[3] Analyze Research Trust Network
[4] Discover Lost Collaboration Opportunities
[5] Identify High-Risk Projects
[6] Analyze Project Research Impact
[7] Recommend Research Partners
[8] Service Status

[0] Return to Main Menu
========================================
        """
        print(menu)

    def find_research_bridge_interactive(self):
        print("\n========================================")
        print("FIND RESEARCH COLLABORATION BRIDGE")
        print("========================================")

        researchers = list(mongodb.db.researchers.find(
            {'profile_status': 'approved'},
            {'name': 1, 'email': 1, 'department': 1}
        ).limit(20))

        if not researchers:
            print("No researchers found in system")
            return

        print("\nAvailable Researchers:")
        for i, researcher in enumerate(researchers, 1):
            print(f"[{i}] {researcher['name']} - {researcher['email']}")

        try:
            choice1 = int(input("\nSelect first researcher (number): ").strip())
            if choice1 < 1 or choice1 > len(researchers):
                print("Invalid selection")
                return

            researcher1 = researchers[choice1 - 1]
            researcher1_id = str(researcher1['_id'])

            choice2 = int(input("Select second researcher (number): ").strip())
            if choice2 < 1 or choice2 > len(researchers) or choice2 == choice1:
                print("Invalid selection")
                return

            researcher2 = researchers[choice2 - 1]
            researcher2_id = str(researcher2['_id'])

            print("\nFinding bridge between:")
            print(f"* {researcher1['name']}")
            print(f"* {researcher2['name']}")
            print("----------------------------------------")

            result = ResearchIntelligenceService.find_research_bridge(
                researcher1_id,
                researcher2_id
            )

            if result['success'] and result['data']:
                data = result['data']
                bridges = data['bridges']

                print(f"\nSUCCESS: Found {len(bridges)} potential bridge(s)")

                for i, bridge in enumerate(bridges, 1):
                    print(f"\nPath {i} (length: {bridge['path_length']}):")

                    for node in bridge['path_details']:
                        if node['type'] == 'researcher':
                            role_symbol = "==>" if node['role'] == 'target' else "--->"
                            print(f"  {role_symbol} {node['name']} ({node['department']})")

                print(f"\nAnalysis Summary:")
                print(f"Researcher 1: {data['researcher1']['name']}")
                print(f"Researcher 2: {data['researcher2']['name']}")
                print(f"Total bridges found: {len(bridges)}")

                if bridges:
                    shortest_path = min(bridges, key=lambda x: x['path_length'])
                    print(f"Shortest path: {shortest_path['path_length']} steps")
            else:
                print(f"FAILED: {result['message']}")

        except ValueError:
            print("Please enter a valid number")
        except Exception as e:
            print(f"Error: {e}")

    def find_hidden_experts_interactive(self):
        print("\n========================================")
        print("FIND HIDDEN EXPERTS IN A FIELD")
        print("========================================")

        research_area = input("Enter research field (e.g., Machine Learning): ").strip()

        if not research_area:
            print("Research field is required")
            return

        limit = input("Number of results (default: 10): ").strip()
        limit = int(limit) if limit.isdigit() else 10

        print(f"\nFinding hidden experts in: {research_area}")
        print("----------------------------------------")

        result = ResearchIntelligenceService.find_hidden_expert(research_area, limit)

        if result['success'] and result['data'] and result['data']['experts']:
            experts = result['data']['experts']

            print(f"\nSUCCESS: Found {len(experts)} hidden experts")

            table_data = []
            for i, expert in enumerate(experts, 1):
                table_data.append([
                    i,
                    expert['name'],
                    expert['department'],
                    expert['publication_count'],
                    expert['total_citations'],
                    expert['unique_collaborators'],
                    f"{expert['hidden_impact_score']:.2f}"
                ])

            headers = ['#', 'Name', 'Department', 'Publications', 'Citations', 'Collaborators', 'Impact Score']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            if experts:
                best_expert = experts[0]
                print(f"\nBEST HIDDEN EXPERT:")
                print(f"* Name: {best_expert['name']}")
                print(f"* Department: {best_expert['department']}")
                print(f"* Impact Score: {best_expert['hidden_impact_score']}")
                print(f"* Top Interests: {', '.join(best_expert['research_interests'][:3])}")

        else:
            print(f"FAILED: {result['message']}")

    def analyze_trust_network_interactive(self):
        print("\n========================================")
        print("ANALYZE RESEARCH TRUST NETWORK")
        print("========================================")

        department = input("Enter department (leave empty for all): ").strip()
        department = department if department else None

        min_collaborations = input("Minimum collaborations (default: 2): ").strip()
        min_collaborations = int(min_collaborations) if min_collaborations.isdigit() else 2

        print("\nAnalyzing trust network...")
        print("----------------------------------------")

        result = ResearchIntelligenceService.analyze_trust_network(department, min_collaborations)

        if result['success'] and result['data']:
            data = result['data']

            print(f"\nSUCCESS: Analyzed {data['total_relationships']} trust relationships")

            print(f"\nTRUST NETWORK STATISTICS:")
            print(f"* Department: {data['department']}")
            print(f"* Total Relationships: {data['total_relationships']}")
            print(f"* Average Collaborations: {data['avg_collaborations']}")
            print(f"* Cross-Department Rate: {data['cross_department_rate']}%")

            if data['trust_hubs']:
                print(f"\nTOP TRUST HUBS:")
                for i, hub in enumerate(data['trust_hubs'][:5], 1):
                    print(f"{i}. {hub['name']} - {hub['department']} (Score: {hub['trust_score']})")

            if data['relationships']:
                print(f"\nSAMPLE TRUST RELATIONSHIPS:")
                for i, rel in enumerate(data['relationships'][:5], 1):
                    print(f"{i}. {rel['researcher1']['name']} <-> {rel['researcher2']['name']}")
                    print(f"   Trust Level: {rel['trust_level']}, Collaborations: {rel['collaboration_count']}")
        else:
            print(f"FAILED: {result['message']}")

    def find_lost_opportunities_interactive(self):
        print("\n========================================")
        print("DISCOVER LOST COLLABORATION OPPORTUNITIES")
        print("========================================")

        min_similarity = input("Minimum similarity % (default: 50): ").strip()
        min_similarity = float(min_similarity) / 100 if min_similarity.isdigit() else 0.5

        print("\nFinding lost opportunities...")
        print("----------------------------------------")

        result = ResearchIntelligenceService.find_lost_opportunities(min_similarity)

        if result['success'] and result['data'] and result['data']['opportunities']:
            opportunities = result['data']['opportunities']

            print(f"\nSUCCESS: Found {len(opportunities)} lost opportunities")

            print(f"\nTOP LOST OPPORTUNITIES:")
            for i, opp in enumerate(opportunities[:10], 1):
                print(f"{i}. {opp['researcher1']['name']} <-> {opp['researcher2']['name']}")
                print(f"   Similarity: {opp['similarity_percentage']}%")
                print(f"   Common Interests: {', '.join(opp['common_interests'][:3])}")
                print(f"   Opportunity Score: {opp['opportunity_score']}")
                print()
        else:
            print(f"FAILED: {result['message']}")

    def identify_high_risk_projects_interactive(self):
        print("\n========================================")
        print("IDENTIFY HIGH-RISK PROJECTS")
        print("========================================")

        risk_threshold = input("Risk threshold (default: 1.5): ").strip()
        risk_threshold = float(risk_threshold) if risk_threshold else 1.5

        print("\nIdentifying high-risk projects...")
        print("----------------------------------------")

        result = ResearchIntelligenceService.identify_high_risk_projects(risk_threshold)

        if result['success'] and result['data'] and result['data']['projects']:
            projects = result['data']['projects']

            print(f"\nSUCCESS: Found {len(projects)} high-risk projects")

            table_data = []
            for i, project in enumerate(projects, 1):
                table_data.append([
                    i,
                    project['title'][:40],
                    project['team_size'],
                    project['department_diversity'],
                    f"{project['collaboration_rate']}%",
                    f"{project['risk_score']:.2f}",
                    project['risk_level']
                ])

            headers = ['#', 'Project Title', 'Team Size', 'Departments', 'Collaboration %', 'Risk Score', 'Level']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            if projects:
                highest_risk = projects[0]
                print(f"\nHIGHEST RISK PROJECT:")
                print(f"* Title: {highest_risk['title']}")
                print(f"* Risk Score: {highest_risk['risk_score']}")
                print(f"* Risk Level: {highest_risk['risk_level']}")
                print(f"* Team Diversity: {highest_risk['department_diversity']} departments")

        else:
            print(f"FAILED: {result['message']}")

    def analyze_project_impact_interactive(self):
        print("\n========================================")
        print("ANALYZE PROJECT RESEARCH IMPACT")
        print("========================================")

        project_id = input("Enter Project ID: ").strip()

        if not project_id:
            print("Project ID is required")
            return

        print("\nAnalyzing project impact...")
        print("----------------------------------------")

        result = ResearchIntelligenceService.analyze_project_research_impact(project_id)

        if result['success'] and result['data']:
            data = result['data']

            print(f"\nSUCCESS: Analyzed project impact")

            print(f"\nPROJECT INFORMATION:")
            print(f"* Title: {data['project_info']['title']}")
            print(f"* Start Date: {data['project_info']['start_date']}")
            print(f"* Team Size: {data['project_info']['team_size']}")

            if data['participant_impact']:
                print(f"\nPARTICIPANT IMPACT ANALYSIS:")

                table_data = []
                for i, participant in enumerate(data['participant_impact'][:10], 1):
                    table_data.append([
                        i,
                        participant['researcher_name'],
                        participant['publications_before'],
                        participant['publications_after'],
                        f"{participant['publication_growth']}%",
                        participant['impact_level']
                    ])

                headers = ['#', 'Researcher', 'Pub Before', 'Pub After', 'Growth %', 'Impact']
                print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

                high_impact = [p for p in data['participant_impact'] if p['impact_level'] == 'High']
                if high_impact:
                    print(f"\nHIGHEST IMPACT PARTICIPANTS:")
                    for participant in high_impact[:3]:
                        print(f"* {participant['researcher_name']}: {participant['publication_growth']}% growth")
        else:
            print(f"FAILED: {result['message']}")

    def recommend_partners_interactive(self):
        print("\n========================================")
        print("RECOMMEND RESEARCH PARTNERS")
        print("========================================")

        researchers = list(mongodb.db.researchers.find(
            {'profile_status': 'approved'},
            {'name': 1, 'email': 1}
        ).limit(20))

        if not researchers:
            print("No researchers found")
            return

        print("\nSelect a researcher:")
        for i, researcher in enumerate(researchers, 1):
            print(f"[{i}] {researcher['name']} - {researcher['email']}")

        try:
            choice = int(input("\nSelect researcher (number): ").strip())
            if choice < 1 or choice > len(researchers):
                print("Invalid selection")
                return

            selected = researchers[choice - 1]
            researcher_id = str(selected['_id'])

            limit = input("Number of recommendations (default: 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5

            print(f"\nFinding partners for: {selected['name']}")
            print("----------------------------------------")

            result = ResearchIntelligenceService.recommend_research_partners(researcher_id, limit)

            if result['success'] and result['data'] and result['data']['recommendations']:
                recommendations = result['data']['recommendations']

                print(f"\nSUCCESS: Found {len(recommendations)} partner recommendations")

                table_data = []
                for i, rec in enumerate(recommendations, 1):
                    table_data.append([
                        i,
                        rec['candidate_name'],
                        rec['candidate_department'],
                        len(rec['common_interests']),
                        len(rec['complementary_interests']),
                        rec['mutual_connections'],
                        f"{rec['recommendation_score']:.3f}",
                        rec['recommendation_level']
                    ])

                headers = ['#', 'Candidate', 'Department', 'Common', 'Complementary', 'Mutual', 'Score', 'Level']
                print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

                if recommendations:
                    best_match = recommendations[0]
                    print(f"\nBEST MATCH:")
                    print(f"* Name: {best_match['candidate_name']}")
                    print(f"* Department: {best_match['candidate_department']}")
                    print(f"* Recommendation Score: {best_match['recommendation_score']}")
                    print(f"* Common Interests: {', '.join(best_match['common_interests'][:3])}")
            else:
                print(f"FAILED: {result['message']}")

        except ValueError:
            print("Please enter a valid number")
        except Exception as e:
            print(f"Error: {e}")

    def show_service_status(self):
        print("\n========================================")
        print("RESEARCH INTELLIGENCE SERVICE STATUS")
        print("========================================")

        status = ResearchIntelligenceService.get_service_status()

        print(f"\nService Information:")
        print(f"* Status: {status['status']}")
        print(f"* Version: {status['version']}")

        print(f"\nSupported Queries:")
        for i, query in enumerate(status['supported_queries'], 1):
            print(f"{i}. {query}")

    def run(self):
        """Main run method"""
        while True:
            try:
                self.display_main_menu()
                choice = input("\nSelect option: ").strip()

                if choice == '0':
                    print("\nReturning to main menu...")
                    break
                elif choice == '1':
                    self.find_research_bridge_interactive()
                elif choice == '2':
                    self.find_hidden_experts_interactive()
                elif choice == '3':
                    self.analyze_trust_network_interactive()
                elif choice == '4':
                    self.find_lost_opportunities_interactive()
                elif choice == '5':
                    self.identify_high_risk_projects_interactive()
                elif choice == '6':
                    self.analyze_project_impact_interactive()
                elif choice == '7':
                    self.recommend_partners_interactive()
                elif choice == '8':
                    self.show_service_status()
                else:
                    print("Invalid choice. Please try again.")

                if choice != '0':
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                break
            except Exception as e:
                print(f"Error: {e}")


@click.command()
def main():
    """Research Analytics CLI"""
    cli = ResearchAnalyticsCLI()
    cli.run()


if __name__ == "__main__":
    main()