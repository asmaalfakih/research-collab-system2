from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from colorama import init, Fore, Style
import click
from tabulate import tabulate

from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.services.researcher_service import ResearcherService
from app.services.project_service import ProjectService
from app.services.publication_service import PublicationService
from app.services.collaboration_service import CollaborationService
from app.services.research_intelligence_service import ResearchIntelligenceService

init(autoreset=True)


class AdminCLI:
    def __init__(self):
        self.current_session = None
        self.current_user = None
        self.mongodb = mongodb

    def login(self):
        """Admin login"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ADMIN LOGIN")
        print(f"{Fore.CYAN}{'=' * 50}")

        email = input(f"{Fore.WHITE}Admin Email: ").strip()
        password = input(f"{Fore.WHITE}Password: ").strip()

        admin_data = mongodb.db.admins.find_one({'email': email})

        if not admin_data:
            print(f"\n{Fore.RED}ERROR: Admin not found")
            return False

        from app.models.researcher import Researcher
        if not Researcher.verify_password(password, admin_data['password']):
            print(f"\n{Fore.RED}ERROR: Invalid password")
            return False

        if admin_data.get('profile_status') != 'approved':
            print(f"\n{Fore.YELLOW}WARNING: Admin account is {admin_data.get('profile_status')}")
            return False

        self.current_user = admin_data
        self.current_user['_id'] = str(admin_data['_id'])
        self.current_user['role'] = 'admin'

        print(f"\n{Fore.GREEN}SUCCESS: Login successful")
        print(f"{Fore.CYAN}Welcome, {admin_data['name']}!")
        return True

    def display_menu(self):
        """Display admin menu with advanced options"""
        menu = f"""
{Fore.CYAN}{'=' * 70}
{Fore.YELLOW}ADMIN DASHBOARD - {self.current_user['name'] if self.current_user else 'Guest'}
{Fore.CYAN}{'=' * 70}

{Fore.GREEN}[1]{Fore.WHITE} Manage Researchers
{Fore.GREEN}[2]{Fore.WHITE} Manage Projects
{Fore.GREEN}[3]{Fore.WHITE} Manage Publications
{Fore.GREEN}[4]{Fore.WHITE} View System Statistics
{Fore.GREEN}[5]{Fore.WHITE} View All Relationships
{Fore.GREEN}[6]{Fore.WHITE} View Top 5 Collaborative Pairs
{Fore.GREEN}[7]{Fore.WHITE} Database Status

{Fore.CYAN}[8]{Fore.WHITE} Advanced Analytics Dashboard
{Fore.CYAN}[9]{Fore.WHITE} Collaboration Intelligence
{Fore.CYAN}[10]{Fore.WHITE} Research Network Analysis

{Fore.GREEN}[0]{Fore.WHITE} Logout & Exit
{Fore.CYAN}{'=' * 70}
        """
        print(menu)

    def advanced_analytics_dashboard(self):
        """Advanced analytics dashboard"""
        while True:
            print(f"\n{Fore.CYAN}{'=' * 60}")
            print(f"{Fore.YELLOW}ADVANCED ANALYTICS DASHBOARD")
            print(f"{Fore.CYAN}{'=' * 60}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} Find Research Bridges")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} Discover Hidden Experts")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Analyze Trust Networks")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Identify Lost Opportunities")
            print(f"{Fore.GREEN}[5]{Fore.WHITE} Detect High-Risk Projects")
            print(f"{Fore.GREEN}[6]{Fore.WHITE} Analyze Project Impact")
            print(f"{Fore.GREEN}[7]{Fore.WHITE} Generate Partner Recommendations")
            print(f"{Fore.GREEN}[8]{Fore.WHITE} Back to main menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

            if choice == '1':
                self.find_research_bridges_admin()
            elif choice == '2':
                self.find_hidden_experts_admin()
            elif choice == '3':
                self.analyze_trust_networks_admin()
            elif choice == '4':
                self.identify_lost_opportunities_admin()
            elif choice == '5':
                self.detect_high_risk_projects_admin()
            elif choice == '6':
                self.analyze_project_impact_admin()
            elif choice == '7':
                self.generate_partner_recommendations_admin()
            elif choice == '8':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def find_research_bridges_admin(self):
        """Find research bridges between researchers"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}FIND RESEARCH COLLABORATION BRIDGES")
        print(f"{Fore.CYAN}{'=' * 50}")

        researchers = list(mongodb.db.researchers.find(
            {'profile_status': 'approved'},
            {'name': 1, 'email': 1, 'department': 1}
        ).limit(20))

        if not researchers:
            print(f"{Fore.YELLOW}No researchers found")
            return

        print(f"\n{Fore.GREEN}Select first researcher:")
        for i, researcher in enumerate(researchers, 1):
            print(f"{Fore.GREEN}[{i}]{Fore.WHITE} {researcher['name']} - {researcher['email']}")

        try:
            choice1 = int(input(f"\n{Fore.YELLOW}Select first researcher (number): ").strip())
            if choice1 < 1 or choice1 > len(researchers):
                print(f"{Fore.RED}Invalid selection")
                return

            print(f"\n{Fore.GREEN}Select second researcher:")
            for i, researcher in enumerate(researchers, 1):
                print(f"{Fore.GREEN}[{i}]{Fore.WHITE} {researcher['name']} - {researcher['email']}")

            choice2 = int(input(f"\n{Fore.YELLOW}Select second researcher (number): ").strip())
            if choice2 < 1 or choice2 > len(researchers) or choice2 == choice1:
                print(f"{Fore.RED}Invalid selection")
                return

            researcher1 = researchers[choice1 - 1]
            researcher2 = researchers[choice2 - 1]
            researcher1_id = str(researcher1['_id'])
            researcher2_id = str(researcher2['_id'])

            print(f"\n{Fore.CYAN}Finding research bridge between:")
            print(f"{Fore.WHITE}• {researcher1['name']}")
            print(f"• {researcher2['name']}")
            print(f"{Fore.CYAN}{'-' * 50}")

            result = ResearchIntelligenceService.find_research_bridge(
                researcher1_id,
                researcher2_id
            )

            if result['success'] and result['data']:
                data = result['data']
                bridges = data['bridges']

                if bridges:
                    print(f"\n{Fore.GREEN}Found {len(bridges)} potential bridge(s)")

                    table_data = []
                    for i, bridge in enumerate(bridges, 1):
                        table_data.append([
                            i,
                            bridge['path_length'],
                            bridge.get('total_bridges', 0),
                            bridge.get('path_details', [])[1]['name'] if len(bridge.get('path_details', [])) > 1 else 'Direct'
                        ])

                    headers = ['#', 'Path Length', 'Total Bridges', 'Main Connector']
                    print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

                    # Show detailed path
                    print(f"\n{Fore.GREEN}Detailed path analysis:")
                    shortest_bridge = min(bridges, key=lambda x: x['path_length'])
                    for node in shortest_bridge.get('path_details', []):
                        if node['type'] == 'researcher':
                            symbol = "➤" if node['role'] == 'target' else "⟶"
                            print(f"{Fore.WHITE}{symbol} {node['name']} ({node['department']})")
                else:
                    print(f"{Fore.YELLOW}No direct bridge found between these researchers")
            else:
                print(f"{Fore.RED}Error: {result.get('message', 'Unknown error')}")

        except ValueError:
            print(f"{Fore.RED}Please enter valid numbers")
        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def find_hidden_experts_admin(self):
        """Find hidden experts in specific fields"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}FIND HIDDEN EXPERTS")
        print(f"{Fore.CYAN}{'=' * 50}")

        research_area = input(f"{Fore.WHITE}Enter research field (e.g., Machine Learning): ").strip()

        if not research_area:
            print(f"{Fore.RED}Research field is required")
            return

        limit = input(f"{Fore.WHITE}Number of results (default: 10): ").strip()
        limit = int(limit) if limit.isdigit() else 10

        print(f"\n{Fore.CYAN}Searching for hidden experts in: {research_area}")
        print(f"{Fore.CYAN}{'-' * 50}")

        result = ResearchIntelligenceService.find_hidden_expert(research_area, limit)

        if result['success'] and result['data'] and result['data']['experts']:
            experts = result['data']['experts']

            print(f"\n{Fore.GREEN}Found {len(experts)} hidden experts")

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

            headers = ['Rank', 'Name', 'Department', 'Publications', 'Citations', 'Collaborators', 'Impact Score']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            # Show top expert details
            top_expert = experts[0]
            print(f"\n{Fore.GREEN}TOP HIDDEN EXPERT:")
            print(f"{Fore.WHITE}Name: {top_expert['name']}")
            print(f"Department: {top_expert['department']}")
            print(f"Impact Score: {top_expert['hidden_impact_score']}")
            print(f"Research Interests: {', '.join(top_expert['research_interests'][:3])}")
        else:
            print(f"{Fore.YELLOW}No hidden experts found in this field")

    def analyze_trust_networks_admin(self):
        """Analyze trust networks in the system"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ANALYZE TRUST NETWORKS")
        print(f"{Fore.CYAN}{'=' * 50}")

        department = input(f"{Fore.WHITE}Enter department (leave empty for all): ").strip()
        department = department if department else None

        min_collaborations = input(f"{Fore.WHITE}Minimum collaborations (default: 2): ").strip()
        min_collaborations = int(min_collaborations) if min_collaborations.isdigit() else 2

        print(f"\n{Fore.CYAN}Analyzing trust network...")
        print(f"{Fore.CYAN}{'-' * 50}")

        result = ResearchIntelligenceService.analyze_trust_network(department, min_collaborations)

        if result['success'] and result['data']:
            data = result['data']

            print(f"\n{Fore.GREEN}TRUST NETWORK ANALYSIS RESULTS:")
            print(f"{Fore.WHITE}Department: {data['department']}")
            print(f"Total Relationships: {data['total_relationships']}")
            print(f"Average Collaborations: {data['avg_collaborations']:.2f}")
            print(f"Cross-Department Rate: {data['cross_department_rate']}%")

            if data.get('trust_hubs'):
                print(f"\n{Fore.GREEN}TOP TRUST HUBS:")
                for i, hub in enumerate(data['trust_hubs'][:5], 1):
                    print(f"{i}. {hub['name']} - {hub['department']} (Trust Score: {hub['trust_score']})")

            if data.get('relationships'):
                print(f"\n{Fore.GREEN}SAMPLE TRUST RELATIONSHIPS:")
                for i, rel in enumerate(data['relationships'][:5], 1):
                    print(f"{i}. {rel['researcher1']['name']} <-> {rel['researcher2']['name']}")
                    print(f"   Trust Level: {rel['trust_level']}, Collaborations: {rel['collaboration_count']}")
        else:
            print(f"{Fore.RED}Error: {result.get('message', 'Unknown error')}")

    def identify_lost_opportunities_admin(self):
        """Identify lost collaboration opportunities"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}IDENTIFY LOST COLLABORATION OPPORTUNITIES")
        print(f"{Fore.CYAN}{'=' * 50}")

        min_similarity = input(f"{Fore.WHITE}Minimum similarity % (default: 50): ").strip()
        min_similarity = float(min_similarity) / 100 if min_similarity.isdigit() else 0.5

        print(f"\n{Fore.CYAN}Analyzing lost opportunities...")
        print(f"{Fore.CYAN}{'-' * 50}")

        result = ResearchIntelligenceService.find_lost_opportunities(min_similarity)

        if result['success'] and result['data'] and result['data']['opportunities']:
            opportunities = result['data']['opportunities']

            print(f"\n{Fore.GREEN}Found {len(opportunities)} lost opportunities")

            print(f"\n{Fore.GREEN}TOP 10 LOST OPPORTUNITIES:")
            for i, opp in enumerate(opportunities[:10], 1):
                print(f"{i}. {opp['researcher1']['name']} <-> {opp['researcher2']['name']}")
                print(f"   Similarity: {opp['similarity_percentage']}%")
                print(f"   Common Interests: {', '.join(opp['common_interests'][:3])}")
                print(f"   Opportunity Score: {opp['opportunity_score']}")
                print()
        else:
            print(f"{Fore.YELLOW}No significant lost opportunities found")

    def detect_high_risk_projects_admin(self):
        """Detect high-risk projects"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}DETECT HIGH-RISK PROJECTS")
        print(f"{Fore.CYAN}{'=' * 50}")

        risk_threshold = input(f"{Fore.WHITE}Risk threshold (default: 1.5): ").strip()
        risk_threshold = float(risk_threshold) if risk_threshold else 1.5

        print(f"\n{Fore.CYAN}Analyzing project risks...")
        print(f"{Fore.CYAN}{'-' * 50}")

        result = ResearchIntelligenceService.identify_high_risk_projects(risk_threshold)

        if result['success'] and result['data'] and result['data']['projects']:
            projects = result['data']['projects']

            print(f"\n{Fore.GREEN}Found {len(projects)} high-risk projects")

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

            # Show highest risk project
            highest_risk = projects[0]
            print(f"\n{Fore.RED}HIGHEST RISK PROJECT:")
            print(f"{Fore.WHITE}Title: {highest_risk['title']}")
            print(f"Risk Score: {highest_risk['risk_score']}")
            print(f"Risk Level: {highest_risk['risk_level']}")
            print(f"Team Diversity: {highest_risk['department_diversity']} departments")
        else:
            print(f"{Fore.GREEN}No high-risk projects detected")

    def analyze_project_impact_admin(self):
        """Analyze project research impact"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ANALYZE PROJECT RESEARCH IMPACT")
        print(f"{Fore.CYAN}{'=' * 50}")

        projects = list(mongodb.db.projects.find(
            {},
            {'title': 1, '_id': 1}
        ).limit(20))

        if not projects:
            print(f"{Fore.YELLOW}No projects found")
            return

        print(f"\n{Fore.GREEN}Select project to analyze:")
        for i, project in enumerate(projects, 1):
            print(f"{Fore.GREEN}[{i}]{Fore.WHITE} {project['title']}")

        try:
            choice = int(input(f"\n{Fore.YELLOW}Select project (number): ").strip())
            if choice < 1 or choice > len(projects):
                print(f"{Fore.RED}Invalid selection")
                return

            project_id = str(projects[choice - 1]['_id'])

            print(f"\n{Fore.CYAN}Analyzing project impact...")
            print(f"{Fore.CYAN}{'-' * 50}")

            result = ResearchIntelligenceService.analyze_project_research_impact(project_id)

            if result['success'] and result['data']:
                data = result['data']

                print(f"\n{Fore.GREEN}PROJECT IMPACT ANALYSIS:")
                print(f"{Fore.WHITE}Title: {data['project_info']['title']}")
                print(f"Start Date: {data['project_info']['start_date']}")
                print(f"Team Size: {data['project_info']['team_size']}")

                if data.get('participant_impact'):
                    print(f"\n{Fore.GREEN}PARTICIPANT IMPACT ANALYSIS:")

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
                        print(f"\n{Fore.GREEN}HIGHEST IMPACT PARTICIPANTS:")
                        for participant in high_impact[:3]:
                            print(f"• {participant['researcher_name']}: {participant['publication_growth']}% growth")
            else:
                print(f"{Fore.RED}Error: {result.get('message', 'Unknown error')}")

        except ValueError:
            print(f"{Fore.RED}Please enter a valid number")

    def generate_partner_recommendations_admin(self):
        """Generate research partner recommendations"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}GENERATE PARTNER RECOMMENDATIONS")
        print(f"{Fore.CYAN}{'=' * 50}")

        researchers = list(mongodb.db.researchers.find(
            {'profile_status': 'approved'},
            {'name': 1, 'email': 1}
        ).limit(20))

        if not researchers:
            print(f"{Fore.YELLOW}No researchers found")
            return

        print(f"\n{Fore.GREEN}Select researcher:")
        for i, researcher in enumerate(researchers, 1):
            print(f"{Fore.GREEN}[{i}]{Fore.WHITE} {researcher['name']} - {researcher['email']}")

        try:
            choice = int(input(f"\n{Fore.YELLOW}Select researcher (number): ").strip())
            if choice < 1 or choice > len(researchers):
                print(f"{Fore.RED}Invalid selection")
                return

            selected = researchers[choice - 1]
            researcher_id = str(selected['_id'])

            limit = input(f"{Fore.WHITE}Number of recommendations (default: 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5

            print(f"\n{Fore.CYAN}Generating recommendations for: {selected['name']}")
            print(f"{Fore.CYAN}{'-' * 50}")

            result = ResearchIntelligenceService.recommend_research_partners(researcher_id, limit)

            if result['success'] and result['data'] and result['data']['recommendations']:
                recommendations = result['data']['recommendations']

                print(f"\n{Fore.GREEN}Found {len(recommendations)} partner recommendations")

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

                headers = ['Rank', 'Candidate', 'Department', 'Common', 'Complementary', 'Mutual', 'Score', 'Level']
                print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

                best_match = recommendations[0]
                print(f"\n{Fore.GREEN}BEST MATCH:")
                print(f"{Fore.WHITE}Name: {best_match['candidate_name']}")
                print(f"Department: {best_match['candidate_department']}")
                print(f"Score: {best_match['recommendation_score']}")
                print(f"Common Interests: {', '.join(best_match['common_interests'][:3])}")
            else:
                print(f"{Fore.YELLOW}No recommendations available for this researcher")

        except ValueError:
            print(f"{Fore.RED}Please enter a valid number")

    def collaboration_intelligence_dashboard(self):
        """Collaboration intelligence dashboard"""
        while True:
            print(f"\n{Fore.CYAN}{'=' * 60}")
            print(f"{Fore.YELLOW}COLLABORATION INTELLIGENCE DASHBOARD")
            print(f"{Fore.CYAN}{'=' * 60}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} Collaboration Network Map")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} Department Collaboration Analysis")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Research Interest Clusters")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Collaboration Trend Analysis")
            print(f"{Fore.GREEN}[5]{Fore.WHITE} Back to main menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

            if choice == '1':
                self.show_collaboration_network_map()
            elif choice == '2':
                self.analyze_department_collaboration()
            elif choice == '3':
                self.analyze_research_clusters()
            elif choice == '4':
                self.analyze_collaboration_trends()
            elif choice == '5':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def show_collaboration_network_map(self):
        """Show collaboration network map"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}COLLABORATION NETWORK MAP")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            from app.services.researcher_service import ResearcherService

            # Get all researchers
            researchers = list(mongodb.db.researchers.find(
                {'profile_status': 'approved'},
                {'name': 1, 'department': 1, '_id': 1}
            ).limit(20))

            if not researchers:
                print(f"{Fore.YELLOW}No researchers found")
                return

            print(f"\n{Fore.GREEN}COLLABORATION NETWORK:")
            print(f"{Fore.WHITE}Total Researchers: {len(researchers)}")

            # Show network statistics
            for researcher in researchers[:5]:
                researcher_id = str(researcher['_id'])
                network = ResearcherService.get_collaboration_network(researcher_id, depth=1)

                if network:
                    print(f"\n{Fore.CYAN}{researcher['name']}:")
                    print(f"{Fore.WHITE}  Connections: {network.get('total_nodes', 0) - 1}")
                    print(f"  Department: {researcher['department']}")

                    if network.get('connections'):
                        print(f"  Top Collaborators:")
                        for conn in network['connections'][:3]:
                            print(f"    • {conn.get('name', 'Unknown')}")

            # Overall network statistics
            with neo4j.driver.session() as session:
                result = session.run("""
                    MATCH ()-[r]-()
                    RETURN 
                        count(DISTINCT r) as total_relationships,
                        avg(r.collaboration_count) as avg_collaborations
                """)

                stats = result.single()
                if stats:
                    print(f"\n{Fore.GREEN}NETWORK STATISTICS:")
                    print(f"{Fore.WHITE}Total Relationships: {stats['total_relationships']}")
                    print(f"Average Collaborations: {stats['avg_collaborations']:.1f}")

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def analyze_department_collaboration(self):
        """Analyze inter-department collaboration"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}DEPARTMENT COLLABORATION ANALYSIS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            with neo4j.driver.session() as session:
                # Get department collaboration matrix
                result = session.run("""
                    MATCH (r1:Researcher)-[rel:CO_AUTHORED_WITH]-(r2:Researcher)
                    WHERE r1.department IS NOT NULL AND r2.department IS NOT NULL
                    RETURN 
                        r1.department as dept1,
                        r2.department as dept2,
                        count(rel) as collaboration_count,
                        avg(rel.collaboration_count) as avg_strength
                    ORDER BY collaboration_count DESC
                    LIMIT 20
                """)

                print(f"\n{Fore.GREEN}TOP DEPARTMENT COLLABORATIONS:")

                table_data = []
                for i, record in enumerate(result, 1):
                    table_data.append([
                        i,
                        record['dept1'],
                        record['dept2'],
                        record['collaboration_count'],
                        f"{record['avg_strength']:.1f}"
                    ])

                headers = ['#', 'Department 1', 'Department 2', 'Collaborations', 'Avg Strength']
                print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

                # Most collaborative departments
                result = session.run("""
                    MATCH (r:Researcher)-[rel:CO_AUTHORED_WITH]-()
                    WITH r.department as department, count(DISTINCT rel) as total_collaborations
                    RETURN department, total_collaborations
                    ORDER BY total_collaborations DESC
                    LIMIT 10
                """)

                print(f"\n{Fore.GREEN}MOST COLLABORATIVE DEPARTMENTS:")

                dept_data = []
                for i, record in enumerate(result, 1):
                    dept_data.append([
                        i,
                        record['department'],
                        record['total_collaborations']
                    ])

                headers = ['Rank', 'Department', 'Total Collaborations']
                print(tabulate(dept_data, headers=headers, tablefmt='simple_grid'))

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def analyze_research_clusters(self):
        """Analyze research interest clusters"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RESEARCH INTEREST CLUSTERS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            # Get all research interests
            pipeline = [
                {"$unwind": "$research_interests"},
                {"$group": {"_id": "$research_interests", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]

            interests = list(mongodb.db.researchers.aggregate(pipeline))

            print(f"\n{Fore.GREEN}TOP RESEARCH INTERESTS:")

            table_data = []
            for i, interest in enumerate(interests, 1):
                table_data.append([
                    i,
                    interest['_id'],
                    interest['count']
                ])

            headers = ['Rank', 'Research Interest', 'Researchers']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            # Show interest clusters
            print(f"\n{Fore.GREEN}INTEREST CLUSTERS:")

            for interest in interests[:5]:
                interest_name = interest['_id']
                print(f"\n{Fore.CYAN}{interest_name} ({interest['count']} researchers):")

                # Find researchers with this interest
                researchers = list(mongodb.db.researchers.find(
                    {'research_interests': interest_name},
                    {'name': 1, 'department': 1}
                ).limit(5))

                for researcher in researchers:
                    print(f"{Fore.WHITE}  • {researcher['name']} ({researcher['department']})")

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def analyze_collaboration_trends(self):
        """Analyze collaboration trends over time"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}COLLABORATION TREND ANALYSIS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            # Get publication trends
            pipeline = [
                {"$group": {"_id": "$year", "count": {"$sum": 1}}},
                {"$sort": {"_id": -1}},
                {"$limit": 10}
            ]

            trends = list(mongodb.db.publications.aggregate(pipeline))

            print(f"\n{Fore.GREEN}PUBLICATION TRENDS BY YEAR:")

            table_data = []
            total_publications = 0
            for i, trend in enumerate(trends, 1):
                table_data.append([
                    i,
                    trend['_id'],
                    trend['count']
                ])
                total_publications += trend['count']

            headers = ['Rank', 'Year', 'Publications']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            print(f"\n{Fore.WHITE}Total publications in last {len(trends)} years: {total_publications}")

            # Collaboration trend
            print(f"\n{Fore.GREEN}COLLABORATION TREND ANALYSIS:")

            # Get average authors per publication
            pipeline = [
                {"$project": {"author_count": {"$size": "$authors"}}},
                {"$group": {"_id": None, "avg_authors": {"$avg": "$author_count"}}}
            ]

            result = list(mongodb.db.publications.aggregate(pipeline))
            if result:
                avg_authors = result[0]['avg_authors']
                print(f"{Fore.WHITE}Average authors per publication: {avg_authors:.1f}")

                if avg_authors > 2:
                    print(f"{Fore.GREEN}Trend: Increasing collaboration (multi-author publications)")
                else:
                    print(f"{Fore.YELLOW}Trend: Limited collaboration (few multi-author publications)")

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def research_network_analysis(self):
        """Advanced research network analysis"""
        while True:
            print(f"\n{Fore.CYAN}{'=' * 60}")
            print(f"{Fore.YELLOW}RESEARCH NETWORK ANALYSIS")
            print(f"{Fore.CYAN}{'=' * 60}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} Network Centrality Analysis")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} Community Detection")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Influential Researchers")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Collaboration Bottlenecks")
            print(f"{Fore.GREEN}[5]{Fore.WHITE} Network Growth Analysis")
            print(f"{Fore.GREEN}[6]{Fore.WHITE} Back to main menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

            if choice == '1':
                self.analyze_network_centrality()
            elif choice == '2':
                self.detect_communities()
            elif choice == '3':
                self.identify_influential_researchers()
            elif choice == '4':
                self.identify_collaboration_bottlenecks()
            elif choice == '5':
                self.analyze_network_growth()
            elif choice == '6':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def analyze_network_centrality(self):
        """Analyze network centrality metrics"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}NETWORK CENTRALITY ANALYSIS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            with neo4j.driver.session() as session:
                # Degree centrality (most connected researchers)
                result = session.run("""
                    MATCH (r:Researcher)-[rel]-()
                    WITH r, count(DISTINCT rel) as degree
                    RETURN r.name as name, degree
                    ORDER BY degree DESC
                    LIMIT 10
                """)

                print(f"\n{Fore.GREEN}DEGREE CENTRALITY (Most Connected):")

                table_data = []
                for i, record in enumerate(result, 1):
                    table_data.append([
                        i,
                        record['name'],
                        record['degree']
                    ])

                headers = ['Rank', 'Researcher', 'Connections']
                print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

                # Betweenness centrality (bridge researchers)
                print(f"\n{Fore.GREEN}BRIDGE RESEARCHERS (Betweenness):")

                result = session.run("""
                    MATCH (r:Researcher)
                    WHERE size((r)-[]-()) > 1
                    WITH r
                    MATCH path = shortestPath((start:Researcher)-[*]-(end:Researcher))
                    WHERE start <> end AND r IN nodes(path)
                    WITH r, count(path) as betweenness
                    RETURN r.name as name, betweenness
                    ORDER BY betweenness DESC
                    LIMIT 10
                """)

                table_data = []
                for i, record in enumerate(result, 1):
                    table_data.append([
                        i,
                        record['name'],
                        record['betweenness']
                    ])

                headers = ['Rank', 'Researcher', 'Bridge Score']
                print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def detect_communities(self):
        """Detect research communities in the network"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}COMMUNITY DETECTION")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            # Simple community detection based on departments
            pipeline = [
                {"$group": {"_id": "$department", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]

            communities = list(mongodb.db.researchers.aggregate(pipeline))

            print(f"\n{Fore.GREEN}RESEARCH COMMUNITIES BY DEPARTMENT:")

            table_data = []
            total_researchers = 0
            for i, community in enumerate(communities, 1):
                table_data.append([
                    i,
                    community['_id'] or 'Unknown',
                    community['count']
                ])
                total_researchers += community['count']

            headers = ['Rank', 'Department', 'Researchers']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            print(f"\n{Fore.WHITE}Total researchers in top communities: {total_researchers}")

            # Analyze inter-community collaboration
            print(f"\n{Fore.GREEN}INTER-COMMUNITY COLLABORATION:")

            with neo4j.driver.session() as session:
                result = session.run("""
                    MATCH (r1:Researcher)-[rel:CO_AUTHORED_WITH]-(r2:Researcher)
                    WHERE r1.department IS NOT NULL AND r2.department IS NOT NULL
                    WITH r1.department as dept1, r2.department as dept2, count(rel) as collaborations
                    WHERE dept1 <> dept2
                    RETURN dept1, dept2, collaborations
                    ORDER BY collaborations DESC
                    LIMIT 10
                """)

                collab_data = []
                for i, record in enumerate(result, 1):
                    collab_data.append([
                        i,
                        record['dept1'],
                        record['dept2'],
                        record['collaborations']
                    ])

                if collab_data:
                    headers = ['Rank', 'From Department', 'To Department', 'Collaborations']
                    print(tabulate(collab_data, headers=headers, tablefmt='simple_grid'))
                else:
                    print(f"{Fore.YELLOW}No inter-department collaboration data available")

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def identify_influential_researchers(self):
        """Identify most influential researchers"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}INFLUENTIAL RESEARCHERS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            # Get researchers with most publications
            pipeline = [
                {"$unwind": "$authors"},
                {"$group": {"_id": "$authors.researcher_id", "publication_count": {"$sum": 1}}},
                {"$sort": {"publication_count": -1}},
                {"$limit": 10}
            ]

            influential = list(mongodb.db.publications.aggregate(pipeline))

            print(f"\n{Fore.GREEN}MOST PUBLISHED RESEARCHERS:")

            table_data = []
            for i, researcher in enumerate(influential, 1):
                researcher_id = researcher['_id']
                if researcher_id:
                    researcher_data = mongodb.get_researcher(researcher_id)
                    if researcher_data:
                        table_data.append([
                            i,
                            researcher_data['name'],
                            researcher['publication_count'],
                            researcher_data['department']
                        ])

            headers = ['Rank', 'Researcher', 'Publications', 'Department']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            # Get researchers with most citations
            pipeline = [
                {"$unwind": "$authors"},
                {"$group": {"_id": "$authors.researcher_id", "total_citations": {"$sum": "$citation_count"}}},
                {"$sort": {"total_citations": -1}},
                {"$limit": 10}
            ]

            cited = list(mongodb.db.publications.aggregate(pipeline))

            print(f"\n{Fore.GREEN}MOST CITED RESEARCHERS:")

            citation_data = []
            for i, researcher in enumerate(cited, 1):
                researcher_id = researcher['_id']
                if researcher_id:
                    researcher_data = mongodb.get_researcher(researcher_id)
                    if researcher_data:
                        citation_data.append([
                            i,
                            researcher_data['name'],
                            researcher['total_citations'],
                            researcher_data['department']
                        ])

            headers = ['Rank', 'Researcher', 'Total Citations', 'Department']
            print(tabulate(citation_data, headers=headers, tablefmt='simple_grid'))

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def identify_collaboration_bottlenecks(self):
        """Identify collaboration bottlenecks"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}COLLABORATION BOTTLENECKS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            with neo4j.driver.session() as session:
                # Find isolated researchers
                result = session.run("""
                    MATCH (r:Researcher)
                    WHERE NOT (r)-[]-()
                    RETURN r.name as name, r.department as department
                    LIMIT 10
                """)

                isolated = list(result)
                if isolated:
                    print(f"\n{Fore.YELLOW}ISOLATED RESEARCHERS (No collaborations):")

                    table_data = []
                    for i, record in enumerate(isolated, 1):
                        table_data.append([
                            i,
                            record['name'],
                            record['department']
                        ])

                    headers = ['#', 'Researcher', 'Department']
                    print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))
                else:
                    print(f"\n{Fore.GREEN}No isolated researchers found")

                # Find single-connection researchers
                result = session.run("""
                    MATCH (r:Researcher)-[rel]-()
                    WITH r, count(DISTINCT rel) as connections
                    WHERE connections = 1
                    RETURN r.name as name, r.department as department
                    LIMIT 10
                """)

                single_connected = list(result)
                if single_connected:
                    print(f"\n{Fore.YELLOW}RESEARCHERS WITH ONLY ONE CONNECTION:")

                    table_data = []
                    for i, record in enumerate(single_connected, 1):
                        table_data.append([
                            i,
                            record['name'],
                            record['department']
                        ])

                    headers = ['#', 'Researcher', 'Department']
                    print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

                # Departments with low collaboration
                result = session.run("""
                    MATCH (r:Researcher)
                    WHERE r.department IS NOT NULL
                    WITH r.department as department, collect(r) as researchers
                    UNWIND researchers as researcher
                    OPTIONAL MATCH (researcher)-[rel]-()
                    WITH department, 
                         size(researchers) as total_researchers,
                         count(DISTINCT rel) as total_connections
                    RETURN department, total_researchers, total_connections,
                           toFloat(total_connections) / total_researchers as connections_per_researcher
                    ORDER BY connections_per_researcher ASC
                    LIMIT 10
                """)

                print(f"\n{Fore.YELLOW}DEPARTMENTS WITH LOW COLLABORATION:")

                dept_data = []
                for i, record in enumerate(result, 1):
                    dept_data.append([
                        i,
                        record['department'],
                        record['total_researchers'],
                        record['total_connections'],
                        f"{record['connections_per_researcher']:.1f}"
                    ])

                headers = ['Rank', 'Department', 'Researchers', 'Connections', 'Connections/Researcher']
                print(tabulate(dept_data, headers=headers, tablefmt='simple_grid'))

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    def analyze_network_growth(self):
        """Analyze network growth over time"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}NETWORK GROWTH ANALYSIS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            # Get researcher growth by month
            pipeline = [
                {
                    "$project": {
                        "year_month": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}}
                    }
                },
                {"$group": {"_id": "$year_month", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
                {"$limit": 12}
            ]

            growth = list(mongodb.db.researchers.aggregate(pipeline))

            print(f"\n{Fore.GREEN}RESEARCHER GROWTH BY MONTH:")

            table_data = []
            total_researchers = 0
            for i, month in enumerate(growth, 1):
                table_data.append([
                    i,
                    month['_id'],
                    month['count']
                ])
                total_researchers += month['count']

            headers = ['#', 'Month', 'New Researchers']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            print(f"\n{Fore.WHITE}Total new researchers in period: {total_researchers}")

            # Project growth
            pipeline = [
                {
                    "$project": {
                        "year_month": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}}
                    }
                },
                {"$group": {"_id": "$year_month", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
                {"$limit": 12}
            ]

            project_growth = list(mongodb.db.projects.aggregate(pipeline))

            print(f"\n{Fore.GREEN}PROJECT GROWTH BY MONTH:")

            proj_data = []
            total_projects = 0
            for i, month in enumerate(project_growth, 1):
                proj_data.append([
                    i,
                    month['_id'],
                    month['count']
                ])
                total_projects += month['count']

            headers = ['#', 'Month', 'New Projects']
            print(tabulate(proj_data, headers=headers, tablefmt='simple_grid'))

            print(f"\n{Fore.WHITE}Total new projects in period: {total_projects}")

            # Calculate growth rate
            if len(growth) > 1:
                first_month = growth[0]['count']
                last_month = growth[-1]['count']
                if first_month > 0:
                    growth_rate = ((last_month - first_month) / first_month) * 100
                    print(f"\n{Fore.GREEN}RESEARCHER GROWTH RATE: {growth_rate:.1f}%")

                    if growth_rate > 0:
                        print(f"{Fore.GREEN}Trend: Positive growth")
                    else:
                        print(f"{Fore.YELLOW}Trend: Negative growth")

        except Exception as e:
            print(f"{Fore.RED}Error: {e}")

    # === Existing methods from original admin_cli.py ===

    def manage_researchers(self):
        """Manage researchers"""
        while True:
            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}MANAGE RESEARCHERS")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} View all researchers")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} View pending approvals")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Approve researcher")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Reject researcher")
            print(f"{Fore.GREEN}[5]{Fore.WHITE} Delete researcher")
            print(f"{Fore.GREEN}[6]{Fore.WHITE} Search researchers")
            print(f"{Fore.GREEN}[7]{Fore.WHITE} Back to main menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

            if choice == '1':
                self.view_all_researchers()
            elif choice == '2':
                self.view_pending_researchers()
            elif choice == '3':
                self.approve_researcher()
            elif choice == '4':
                self.reject_researcher()
            elif choice == '5':
                self.delete_researcher_safe()
            elif choice == '6':
                self.search_researchers_admin()
            elif choice == '7':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def view_all_researchers(self):
        """View all researchers"""
        researchers = list(mongodb.db.researchers.find(
            {'profile_status': {'$ne': 'deleted'}},
            {'name': 1, 'email': 1, 'department': 1, 'profile_status': 1, 'role': 1}
        ).sort('name', 1))

        if not researchers:
            print(f"\n{Fore.YELLOW}No researchers found")
            return

        print(f"\n{Fore.GREEN}All Researchers ({len(researchers)}):")

        table_data = []
        for i, researcher in enumerate(researchers, 1):
            table_data.append([
                i,
                researcher['name'],
                researcher['email'],
                researcher['department'],
                researcher['profile_status'],
                researcher.get('role', 'researcher')
            ])

        headers = ['No', 'Name', 'Email', 'Department', 'Status', 'Role']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def view_pending_researchers(self):
        """View pending researchers"""
        researchers = list(mongodb.db.researchers.find(
            {'profile_status': 'pending'},
            {'name': 1, 'email': 1, 'department': 1, 'research_interests': 1, 'created_at': 1}
        ).sort('created_at', 1))

        if not researchers:
            print(f"\n{Fore.YELLOW}No pending researchers")
            return

        print(f"\n{Fore.GREEN}Pending Researchers ({len(researchers)}):")

        table_data = []
        for i, researcher in enumerate(researchers, 1):
            interests = researcher.get('research_interests', [])
            interests_str = ', '.join(interests[:3]) if interests else 'None'
            if len(interests) > 3:
                interests_str += '...'

            created = researcher.get('created_at', '')
            created_str = created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else str(created)[:10]

            table_data.append([
                i,
                researcher['name'],
                researcher['email'],
                researcher['department'],
                interests_str,
                created_str
            ])

        headers = ['No', 'Name', 'Email', 'Department', 'Interests', 'Created']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def approve_researcher(self):
        """Approve a researcher"""
        researchers = list(mongodb.db.researchers.find(
            {'profile_status': 'pending'},
            {'name': 1, 'email': 1, '_id': 1}
        ))

        if not researchers:
            print(f"\n{Fore.YELLOW}No pending researchers to approve")
            return

        print(f"\n{Fore.GREEN}Pending Researchers:")

        for i, researcher in enumerate(researchers, 1):
            print(f"{Fore.GREEN}[{i}]{Fore.WHITE} {researcher['name']} - {researcher['email']}")

        try:
            choice = int(input(f"\n{Fore.YELLOW}Select researcher to approve (number): ").strip())
            if choice < 1 or choice > len(researchers):
                print(f"{Fore.RED}Invalid choice")
                return

            selected = researchers[choice - 1]
            researcher_id = str(selected['_id'])

            confirm = input(f"\n{Fore.YELLOW}Approve {selected['name']}? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print(f"{Fore.YELLOW}Approval cancelled")
                return

            success, message = ResearcherService.update_researcher_status(
                researcher_id,
                'approved',
                self.current_user['_id']
            )

            if success:
                print(f"{Fore.GREEN}SUCCESS: {message}")
            else:
                print(f"{Fore.RED}ERROR: {message}")

        except ValueError:
            print(f"{Fore.RED}ERROR: Please enter a valid number")

    def reject_researcher(self):
        """Reject a researcher"""
        researchers = list(mongodb.db.researchers.find(
            {'profile_status': 'pending'},
            {'name': 1, 'email': 1, '_id': 1}
        ))

        if not researchers:
            print(f"\n{Fore.YELLOW}No pending researchers to reject")
            return

        print(f"\n{Fore.GREEN}Pending Researchers:")

        for i, researcher in enumerate(researchers, 1):
            print(f"{Fore.GREEN}[{i}]{Fore.WHITE} {researcher['name']} - {researcher['email']}")

        try:
            choice = int(input(f"\n{Fore.YELLOW}Select researcher to reject (number): ").strip())
            if choice < 1 or choice > len(researchers):
                print(f"{Fore.RED}Invalid choice")
                return

            selected = researchers[choice - 1]
            researcher_id = str(selected['_id'])

            confirm = input(f"\n{Fore.RED}Reject {selected['name']}? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print(f"{Fore.YELLOW}Rejection cancelled")
                return

            success, message = ResearcherService.update_researcher_status(
                researcher_id,
                'rejected',
                self.current_user['_id']
            )

            if success:
                print(f"{Fore.GREEN}SUCCESS: {message}")
            else:
                print(f"{Fore.RED}ERROR: {message}")

        except ValueError:
            print(f"{Fore.RED}ERROR: Please enter a valid number")

    def delete_researcher_safe(self):
        """Delete researcher using the safe function"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}DELETE RESEARCHER (SAFE MODE)")
        print(f"{Fore.CYAN}{'=' * 50}")

        # خيارات البحث
        print(f"\n{Fore.GREEN}How do you want to find the researcher?")
        print(f"{Fore.GREEN}[1]{Fore.WHITE} Search by email")
        print(f"{Fore.GREEN}[2]{Fore.WHITE} Search by name")
        print(f"{Fore.GREEN}[3]{Fore.WHITE} List all researchers")

        choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

        researcher_identifier = None

        if choice == '1':
            # البحث بالإيميل
            email = input(f"{Fore.WHITE}Enter researcher email: ").strip()
            if email:
                researcher_identifier = email

        elif choice == '2':
            # البحث بالاسم
            name = input(f"{Fore.WHITE}Enter researcher name (or part of it): ").strip()
            if name:
                # البحث في MongoDB
                researchers = list(mongodb.db.researchers.find(
                    {
                        'name': {'$regex': f'.*{name}.*', '$options': 'i'},
                        'profile_status': {'$ne': 'deleted'}
                    },
                    {'name': 1, 'email': 1, '_id': 1}
                ).limit(10))

                if not researchers:
                    print(f"{Fore.YELLOW}No researchers found")
                    return

                print(f"\n{Fore.GREEN}Found researchers:")
                for i, r in enumerate(researchers, 1):
                    print(f"{Fore.GREEN}[{i}]{Fore.WHITE} {r['name']} - {r['email']}")

                try:
                    idx = int(input(f"\n{Fore.YELLOW}Select researcher (number): ").strip()) - 1
                    if 0 <= idx < len(researchers):
                        researcher_identifier = str(researchers[idx]['_id'])
                    else:
                        print(f"{Fore.RED}Invalid choice")
                        return
                except:
                    print(f"{Fore.RED}Invalid input")
                    return

        elif choice == '3':
            # عرض جميع الباحثين
            researchers = list(mongodb.db.researchers.find(
                {'profile_status': {'$ne': 'deleted'}},
                {'name': 1, 'email': 1, '_id': 1}
            ).sort('name', 1))

            if not researchers:
                print(f"{Fore.YELLOW}No researchers found")
                return

            print(f"\n{Fore.GREEN}All researchers ({len(researchers)}):")
            for i, r in enumerate(researchers, 1):
                print(f"{Fore.GREEN}[{i}]{Fore.WHITE} {r['name']} - {r['email']}")

            try:
                idx = int(input(f"\n{Fore.YELLOW}Select researcher to delete (number): ").strip()) - 1
                if 0 <= idx < len(researchers):
                    researcher_identifier = str(researchers[idx]['_id'])
                else:
                    print(f"{Fore.RED}Invalid choice")
                    return
            except:
                print(f"{Fore.RED}Invalid input")
                return

        else:
            print(f"{Fore.RED}Invalid choice")
            return

        if not researcher_identifier:
            print(f"{Fore.RED}No researcher selected")
            return

        # التأكيد النهائي
        confirm = input(
            f"\n{Fore.RED}⚠️ ARE YOU SURE YOU WANT TO DELETE THIS RESEARCHER? (type 'DELETE' to confirm): ").strip()

        if confirm != 'DELETE':
            print(f"{Fore.YELLOW}❌ Deletion cancelled")
            return

        # استخدام الدالة الآمنة للحذف
        success, message = ResearcherService.delete_researcher_safe(researcher_identifier, self.current_user['_id'])

        if success:
            print(f"\n{Fore.GREEN}{message}")
        else:
            print(f"\n{Fore.RED}{message}")

        input(f"\n{Fore.CYAN}Press Enter to continue...")

    def search_researchers_admin(self):
        """Search researchers for admin"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}SEARCH RESEARCHERS")
        print(f"{Fore.CYAN}{'=' * 50}")

        query = input(f"{Fore.WHITE}Search (name, email, department): ").strip()

        researchers = list(mongodb.db.researchers.find(
            {
                '$and': [
                    {'profile_status': {'$ne': 'deleted'}},
                    {'$or': [
                        {'name': {'$regex': f'.*{query}.*', '$options': 'i'}},
                        {'email': {'$regex': f'.*{query}.*', '$options': 'i'}},
                        {'department': {'$regex': f'.*{query}.*', '$options': 'i'}}
                    ]}
                ]
            },
            {'name': 1, 'email': 1, 'department': 1, 'profile_status': 1}
        ).limit(20))

        if not researchers:
            print(f"\n{Fore.YELLOW}No researchers found")
            return

        print(f"\n{Fore.GREEN}Found {len(researchers)} researcher(s):")

        table_data = []
        for i, researcher in enumerate(researchers, 1):
            table_data.append([
                i,
                researcher['name'],
                researcher['email'],
                researcher['department'],
                researcher['profile_status']
            ])

        headers = ['No', 'Name', 'Email', 'Department', 'Status']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

        print(f"\n{Fore.GREEN}[V]#{Fore.WHITE} View details")
        print(f"{Fore.GREEN}[A]#{Fore.WHITE} Approve")
        print(f"{Fore.GREEN}[R]#{Fore.WHITE} Reject")
        print(f"{Fore.GREEN}[D]#{Fore.WHITE} Delete")
        print(f"{Fore.GREEN}[B]{Fore.WHITE} Back")

        choice = input(f"\n{Fore.YELLOW}Select option: ").upper()

        if choice.startswith('V') and choice[1:].isdigit():
            idx = int(choice[1:]) - 1
            if 0 <= idx < len(researchers):
                self.view_researcher_details(str(researchers[idx]['_id']))
        elif choice.startswith('A') and choice[1:].isdigit():
            idx = int(choice[1:]) - 1
            if 0 <= idx < len(researchers):
                researcher_id = str(researchers[idx]['_id'])
                success, msg = ResearcherService.update_researcher_status(
                    researcher_id, 'approved', self.current_user['_id']
                )
                print(f"{Fore.GREEN if success else Fore.RED}{msg}")
        elif choice.startswith('R') and choice[1:].isdigit():
            idx = int(choice[1:]) - 1
            if 0 <= idx < len(researchers):
                researcher_id = str(researchers[idx]['_id'])
                success, msg = ResearcherService.update_researcher_status(
                    researcher_id, 'rejected', self.current_user['_id']
                )
                print(f"{Fore.GREEN if success else Fore.RED}{msg}")
        elif choice.startswith('D') and choice[1:].isdigit():
            idx = int(choice[1:]) - 1
            if 0 <= idx < len(researchers):
                researcher_id = str(researchers[idx]['_id'])
                success, msg = ResearcherService.delete_researcher_safe(
                    researcher_id, self.current_user['_id']
                )
                print(f"{Fore.GREEN if success else Fore.RED}{msg}")

    def view_researcher_details(self, researcher_id: str):
        """View detailed researcher information"""
        researcher = mongodb.get_researcher(researcher_id)

        if not researcher:
            print(f"{Fore.RED}Researcher not found")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}RESEARCHER DETAILS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}Basic Information:")
        print(f"{Fore.WHITE}  Name: {researcher.get('name', 'N/A')}")
        print(f"  Email: {researcher.get('email', 'N/A')}")
        print(f"  Department: {researcher.get('department', 'N/A')}")
        print(f"  Status: {researcher.get('profile_status', 'N/A')}")
        print(f"  Role: {researcher.get('role', 'researcher')}")

        interests = researcher.get('research_interests', [])
        if interests:
            print(f"  Research Interests: {', '.join(interests)}")

        contact = researcher.get('contact', {})
        if contact:
            print(f"  Phone: {contact.get('phone', 'N/A')}")
            print(f"  City: {contact.get('city', 'N/A')}")

        print(f"\n{Fore.GREEN}Activity:")
        print(f"{Fore.WHITE}  Created: {researcher.get('created_at', 'N/A')}")
        print(f"  Last Login: {researcher.get('last_login', 'N/A')}")
        print(f"  Login Count: {researcher.get('login_count', 0)}")

        # Get projects count
        projects_count = mongodb.db.projects.count_documents({
            'participants': researcher_id
        })

        # Get publications count
        publications_count = mongodb.db.publications.count_documents({
            'authors.researcher_id': researcher_id
        })

        print(f"\n{Fore.GREEN}Statistics:")
        print(f"{Fore.WHITE}  Projects: {projects_count}")
        print(f"  Publications: {publications_count}")

        input(f"\n{Fore.CYAN}Press Enter to continue...")

    def manage_projects(self):
        """Manage projects"""
        while True:
            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}MANAGE PROJECTS")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} View all projects")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} View project details")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Delete project")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Back to main menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

            if choice == '1':
                self.view_all_projects()
            elif choice == '2':
                self.view_project_details_admin()
            elif choice == '3':
                self.delete_project_admin()
            elif choice == '4':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def view_all_projects(self):
        """View all projects"""
        projects = list(mongodb.db.projects.find(
            {},
            {'title': 1, 'creator_name': 1, 'status': 1, 'research_area': 1, 'created_at': 1}
        ).sort('created_at', -1).limit(20))

        if not projects:
            print(f"\n{Fore.YELLOW}No projects found")
            return

        print(f"\n{Fore.GREEN}All Projects ({len(projects)}):")

        table_data = []
        for i, project in enumerate(projects, 1):
            created = project.get('created_at', '')
            created_str = created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else str(created)[:10]

            table_data.append([
                i,
                project.get('title', 'N/A')[:40],
                project.get('creator_name', 'N/A')[:20],
                project.get('status', 'N/A'),
                project.get('research_area', 'N/A')[:20],
                created_str
            ])

        headers = ['No', 'Title', 'Creator', 'Status', 'Research Area', 'Created']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def view_project_details_admin(self):
        """View project details"""
        project_id = input(f"{Fore.WHITE}Enter project ID: ").strip()

        if not project_id:
            print(f"{Fore.RED}Project ID is required")
            return

        project = mongodb.get_project(project_id)

        if not project:
            print(f"{Fore.RED}Project not found")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}PROJECT DETAILS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}Basic Information:")
        print(f"{Fore.WHITE}  Title: {project.get('title', 'N/A')}")
        print(f"  Creator: {project.get('creator_name', 'N/A')}")
        print(f"  Status: {project.get('status', 'N/A')}")
        print(f"  Research Area: {project.get('research_area', 'N/A')}")

        print(f"\n{Fore.GREEN}Participants ({len(project.get('participants', []))}):")
        for participant_id in project.get('participants', []):
            participant = mongodb.get_researcher(participant_id)
            if participant:
                print(f"{Fore.WHITE}  • {participant.get('name', 'Unknown')}")

    def delete_project_admin(self):
        """Delete project as admin"""
        project_id = input(f"{Fore.WHITE}Enter project ID to delete: ").strip()

        if not project_id:
            print(f"{Fore.RED}Project ID is required")
            return

        project = mongodb.get_project(project_id)

        if not project:
            print(f"{Fore.RED}Project not found")
            return

        confirm = input(f"\n{Fore.RED}Delete project '{project.get('title', 'N/A')}'? (type 'DELETE'): ").strip()

        if confirm != 'DELETE':
            print(f"{Fore.YELLOW}Deletion cancelled")
            return

        from app.services.project_service import ProjectService
        success, message = ProjectService.delete_project(project_id, self.current_user['_id'])

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def manage_publications(self):
        """Manage publications"""
        while True:
            print(f"\n{Fore.CYAN}{'=' * 50}")
            print(f"{Fore.YELLOW}MANAGE PUBLICATIONS")
            print(f"{Fore.CYAN}{'=' * 50}")

            print(f"\n{Fore.GREEN}[1]{Fore.WHITE} View all publications")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} View publication details")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Delete publication")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Back to main menu")

            choice = input(f"\n{Fore.YELLOW}Select option: ").strip()

            if choice == '1':
                self.view_all_publications()
            elif choice == '2':
                self.view_publication_details_admin()
            elif choice == '3':
                self.delete_publication_admin()
            elif choice == '4':
                break
            else:
                print(f"{Fore.RED}ERROR: Invalid choice")

    def view_all_publications(self):
        """View all publications"""
        publications = list(mongodb.db.publications.find(
            {},
            {'title': 1, 'year': 1, 'journal': 1, 'citation_count': 1}
        ).sort('year', -1).limit(20))

        if not publications:
            print(f"\n{Fore.YELLOW}No publications found")
            return

        print(f"\n{Fore.GREEN}All Publications ({len(publications)}):")

        table_data = []
        for i, pub in enumerate(publications, 1):
            table_data.append([
                i,
                pub.get('title', 'N/A')[:50],
                pub.get('year', 'N/A'),
                pub.get('journal', 'N/A')[:20],
                pub.get('citation_count', 0)
            ])

        headers = ['No', 'Title', 'Year', 'Journal', 'Citations']
        print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

    def view_publication_details_admin(self):
        """View publication details"""
        publication_id = input(f"{Fore.WHITE}Enter publication ID: ").strip()

        if not publication_id:
            print(f"{Fore.RED}Publication ID is required")
            return

        publication = mongodb.db.publications.find_one({'_id': ObjectId(publication_id)})

        if not publication:
            print(f"{Fore.RED}Publication not found")
            return

        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}PUBLICATION DETAILS")
        print(f"{Fore.CYAN}{'=' * 50}")

        print(f"\n{Fore.GREEN}Basic Information:")
        print(f"{Fore.WHITE}  Title: {publication.get('title', 'N/A')}")
        print(f"  Year: {publication.get('year', 'N/A')}")
        print(f"  Journal: {publication.get('journal', 'N/A')}")

        print(f"\n{Fore.GREEN}Authors:")
        for author in publication.get('authors', []):
            if isinstance(author, dict):
                print(f"{Fore.WHITE}  • {author.get('name', 'Unknown')}")

    def delete_publication_admin(self):
        """Delete publication as admin"""
        publication_id = input(f"{Fore.WHITE}Enter publication ID to delete: ").strip()

        if not publication_id:
            print(f"{Fore.RED}Publication ID is required")
            return

        publication = mongodb.db.publications.find_one({'_id': ObjectId(publication_id)})

        if not publication:
            print(f"{Fore.RED}Publication not found")
            return

        confirm = input(
            f"\n{Fore.RED}Delete publication '{publication.get('title', 'N/A')}'? (type 'DELETE'): ").strip()

        if confirm != 'DELETE':
            print(f"{Fore.YELLOW}Deletion cancelled")
            return

        from app.services.publication_service import PublicationService
        success, message = PublicationService.delete_publication(publication_id, self.current_user['_id'])

        if success:
            print(f"{Fore.GREEN}SUCCESS: {message}")
        else:
            print(f"{Fore.RED}ERROR: {message}")

    def view_system_statistics(self):
        """View system statistics"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}SYSTEM STATISTICS")
        print(f"{Fore.CYAN}{'=' * 50}")

        # Count documents
        researchers_count = mongodb.db.researchers.count_documents({'profile_status': {'$ne': 'deleted'}})
        projects_count = mongodb.db.projects.count_documents({})
        publications_count = mongodb.db.publications.count_documents({})
        admins_count = mongodb.db.admins.count_documents({})

        print(f"\n{Fore.GREEN}Database Statistics:")
        print(f"{Fore.WHITE}  Active Researchers: {researchers_count}")
        print(f"  Total Projects: {projects_count}")
        print(f"  Total Publications: {publications_count}")
        print(f"  Administrators: {admins_count}")

        # Neo4j statistics
        if neo4j and hasattr(neo4j, 'driver') and neo4j.driver:
            try:
                with neo4j.driver.session() as session:
                    result = session.run("MATCH (r:Researcher) RETURN count(r) as count")
                    neo4j_researchers = result.single()["count"]

                    result = session.run("MATCH ()-[r]-() RETURN count(r) as count")
                    relationships = result.single()["count"]

                    print(f"\n{Fore.GREEN}Neo4j Graph Statistics:")
                    print(f"{Fore.WHITE}  Researcher Nodes: {neo4j_researchers}")
                    print(f"  Total Relationships: {relationships}")
            except Exception as e:
                print(f"\n{Fore.YELLOW}Neo4j Statistics: Error - {e}")

        # Redis statistics
        if redis_manager and redis_manager.is_connected():
            try:
                keys = redis_manager.client.keys("*")
                print(f"\n{Fore.GREEN}Redis Cache Statistics:")
                print(f"{Fore.WHITE}  Total Keys: {len(keys)}")
            except:
                pass

    def view_all_relationships(self):
        """View all relationships"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}ALL RELATIONSHIPS")
        print(f"{Fore.CYAN}{'=' * 50}")

        try:
            from app.services.collaboration_service import CollaborationService
            relationships = CollaborationService.get_all_relationships()

            if not relationships:
                print(f"\n{Fore.YELLOW}No relationships found")
                return

            print(f"\n{Fore.GREEN}Total Relationships: {len(relationships)}")

            # Group by relationship type
            type_counts = {}
            for rel in relationships:
                rel_type = rel.get('relationship_type', 'Unknown')
                type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

            print(f"\n{Fore.GREEN}By Type:")
            for rel_type, count in sorted(type_counts.items()):
                print(f"{Fore.WHITE}  {rel_type}: {count}")

            # Show sample relationships
            print(f"\n{Fore.GREEN}Sample Relationships (first 10):")
            for i, rel in enumerate(relationships[:10], 1):
                if 'researcher1_name' in rel and 'researcher2_name' in rel:
                    print(
                        f"{Fore.WHITE}  {i}. {rel['researcher1_name']} <-> {rel['researcher2_name']} ({rel['relationship_type']})")
                elif 'researcher_name' in rel and 'project_title' in rel:
                    print(
                        f"{Fore.WHITE}  {i}. {rel['researcher_name']} -> {rel['project_title']} ({rel['relationship_type']})")

        except Exception as e:
            print(f"{Fore.RED}Error loading relationships: {e}")

    def view_top_collaborative_pairs(self):
        """View Top 5 Collaborative Pairs in Admin Dashboard"""
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}TOP 5 COLLABORATIVE PAIRS - ADMIN VIEW")
        print(f"{Fore.CYAN}{'=' * 60}")

        try:
            from app.services.collaboration_service import CollaborationService
            from tabulate import tabulate

            print(f"{Fore.YELLOW}Fetching collaboration data from Neo4j...")

            # الحصول على أفضل 5 أزواج من Neo4j
            pairs = CollaborationService.get_most_collaborative_pairs(5)

            if not pairs:
                print(f"{Fore.YELLOW}No collaborative pairs found in the database.")
                print(f"{Fore.CYAN}Try creating some co-authorship relationships first.")
                return

            print(f"\n{Fore.GREEN}Top 5 Most Collaborative Researcher Pairs:")
            print(f"{Fore.WHITE}(Based on CO_AUTHORED_WITH relationship count)")

            table_data = []
            total_collaborations = 0
            total_publications = 0

            for i, pair in enumerate(pairs, 1):
                collaboration_count = pair.get('collaboration_count', 0)
                publications_count = pair.get('publications_count', 0)

                total_collaborations += collaboration_count
                total_publications += publications_count

                table_data.append([
                    i,
                    f"{pair.get('researcher1_name', 'Unknown')}",
                    f"{pair.get('researcher2_name', 'Unknown')}",
                    collaboration_count,
                    publications_count,
                    pair.get('last_collaboration', 'N/A')
                ])

            headers = ['Rank', 'Researcher 1', 'Researcher 2', 'Collaborations', 'Publications', 'Last Collaboration']
            print(tabulate(table_data, headers=headers, tablefmt='simple_grid'))

            print(f"\n{Fore.GREEN}SUMMARY STATISTICS:")
            print(f"{Fore.WHITE}Total pairs analyzed: {len(pairs)}")
            print(f"{Fore.WHITE}Total collaborations: {total_collaborations}")
            print(f"{Fore.WHITE}Total publications: {total_publications}")

            if len(pairs) > 0:
                avg_collaborations = total_collaborations / len(pairs)
                avg_publications = total_publications / len(pairs)
                print(f"{Fore.WHITE}Average collaborations per pair: {avg_collaborations:.1f}")
                print(f"{Fore.WHITE}Average publications per pair: {avg_publications:.1f}")

            # عرض الأزواج الأكثر نشاطاً في المشاريع
            print(f"\n{Fore.CYAN}{'-' * 60}")
            print(f"{Fore.YELLOW}TOP 5 ACTIVE TEAMWORK PAIRS")
            print(f"{Fore.CYAN}{'-' * 60}")

            teams = CollaborationService.get_most_active_teams(5)

            if teams:
                team_table_data = []
                total_team_collaborations = 0
                total_projects = 0

                for i, team in enumerate(teams, 1):
                    team_collaborations = team.get('collaboration_count', 0)
                    team_projects = team.get('projects_count', 0)

                    total_team_collaborations += team_collaborations
                    total_projects += team_projects

                    team_table_data.append([
                        i,
                        f"{team.get('researcher1_name', 'Unknown')}",
                        f"{team.get('researcher2_name', 'Unknown')}",
                        team_collaborations,
                        team_projects,
                        team.get('last_collaboration', 'N/A')
                    ])

                team_headers = ['Rank', 'Team Member 1', 'Team Member 2', 'Collaborations', 'Projects',
                                'Last Collaboration']
                print(tabulate(team_table_data, headers=team_headers, tablefmt='simple_grid'))

                print(f"\n{Fore.GREEN}TEAMWORK SUMMARY:")
                print(f"{Fore.WHITE}Total team pairs: {len(teams)}")
                print(f"{Fore.WHITE}Total team collaborations: {total_team_collaborations}")
                print(f"{Fore.WHITE}Total projects: {total_projects}")

                if len(teams) > 0:
                    avg_team_collaborations = total_team_collaborations / len(teams)
                    avg_projects_per_team = total_projects / len(teams)
                    print(f"{Fore.WHITE}Average team collaborations: {avg_team_collaborations:.1f}")
                    print(f"{Fore.WHITE}Average projects per team: {avg_projects_per_team:.1f}")
            else:
                print(f"{Fore.YELLOW}No teamwork data available")

            print(f"\n{Fore.CYAN}{'=' * 60}")
            print(f"{Fore.GREEN}DATA ANALYSIS:")
            print(f"{Fore.WHITE}• Co-authorship pairs show researchers who frequently publish together")
            print(f"{Fore.WHITE}• Teamwork pairs show researchers who collaborate on projects")
            print(f"{Fore.WHITE}• Data is retrieved directly from Neo4j graph database")
            print(f"{Fore.WHITE}• Cached in Redis for performance")
            print(f"{Fore.CYAN}{'=' * 60}")

            # خيارات إضافية للمسؤول
            print(f"\n{Fore.YELLOW}ADMIN ACTIONS:")
            print(f"{Fore.GREEN}[1]{Fore.WHITE} Refresh cache")
            print(f"{Fore.GREEN}[2]{Fore.WHITE} View raw data")
            print(f"{Fore.GREEN}[3]{Fore.WHITE} Export to file")
            print(f"{Fore.GREEN}[4]{Fore.WHITE} Back to menu")

            action = input(f"\n{Fore.YELLOW}Select action: ").strip()

            if action == '1':
                # تحديث الكاش
                if redis_manager.is_connected():
                    redis_manager.cache_delete_pattern("collaboration_pairs:*")
                    redis_manager.cache_delete_pattern("active_teams:*")
                    print(f"{Fore.GREEN}Cache cleared successfully")
                else:
                    print(f"{Fore.YELLOW}Redis cache is not connected")

            elif action == '2':
                # عرض البيانات الخام
                print(f"\n{Fore.CYAN}RAW PAIRS DATA:")
                for i, pair in enumerate(pairs, 1):
                    print(f"\n{Fore.GREEN}Pair #{i}:")
                    print(f"{Fore.WHITE}  Researcher 1 ID: {pair.get('researcher1_id')}")
                    print(f"  Researcher 1 Name: {pair.get('researcher1_name')}")
                    print(f"  Researcher 2 ID: {pair.get('researcher2_id')}")
                    print(f"  Researcher 2 Name: {pair.get('researcher2_name')}")
                    print(f"  Collaboration Count: {pair.get('collaboration_count')}")
                    print(f"  Publications Count: {pair.get('publications_count')}")
                    print(f"  Last Collaboration: {pair.get('last_collaboration')}")
                    print(f"  Relationship Type: {pair.get('relationship_type')}")

            elif action == '3':
                # تصدير إلى ملف
                import json
                from datetime import datetime

                export_data = {
                    'export_time': datetime.now().isoformat(),
                    'total_pairs': len(pairs),
                    'pairs': pairs,
                    'teams': teams if teams else []
                }

                filename = f"top_pairs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)

                print(f"{Fore.GREEN}Data exported to {filename}")

        except ImportError as e:
            print(f"{Fore.RED}Error: Cannot import CollaborationService: {e}")
            print(f"{Fore.YELLOW}Make sure collaboration_service.py is properly configured")
        except Exception as e:
            print(f"{Fore.RED}Error showing top collaborative pairs: {e}")

    def database_status(self):
        """Check database status"""
        print(f"\n{Fore.CYAN}{'=' * 50}")
        print(f"{Fore.YELLOW}DATABASE STATUS")
        print(f"{Fore.CYAN}{'=' * 50}")

        # MongoDB
        try:
            mongodb.client.admin.command('ping')
            print(f"\n{Fore.GREEN}MongoDB: ✓ Connected")
            print(f"{Fore.WHITE}  Database: {mongodb.db.name}")
            collections = mongodb.db.list_collection_names()
            print(f"  Collections: {len(collections)}")
        except Exception as e:
            print(f"\n{Fore.RED}MongoDB: ✗ Error: {e}")

        # Neo4j
        if neo4j and hasattr(neo4j, 'driver'):
            try:
                with neo4j.driver.session() as session:
                    session.run("RETURN 1")
                    print(f"\n{Fore.GREEN}Neo4j: ✓ Connected")
            except Exception as e:
                print(f"\n{Fore.RED}Neo4j: ✗ Error: {e}")
        else:
            print(f"\n{Fore.YELLOW}Neo4j: ⚠ Not initialized")

        # Redis
        if redis_manager and redis_manager.is_connected():
            print(f"\n{Fore.GREEN}Redis: ✓ Connected")
            try:
                info = redis_manager.get_system_stats()
                if info.get('status') == 'connected':
                    print(f"{Fore.WHITE}  Version: {info.get('version', 'N/A')}")
                    print(f"  Memory: {info.get('memory_used', 'N/A')}")
            except:
                pass
        else:
            print(f"\n{Fore.YELLOW}Redis: ⚠ Disabled or not connected")

    def run(self):
        """Run admin interface with advanced analytics"""
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
                    self.manage_researchers()
                elif choice == '2':
                    self.manage_projects()
                elif choice == '3':
                    self.manage_publications()
                elif choice == '4':
                    self.view_system_statistics()
                elif choice == '5':
                    self.view_all_relationships()
                elif choice == '6':
                    self.view_top_collaborative_pairs()
                elif choice == '7':
                    self.database_status()
                elif choice == '8':
                    self.advanced_analytics_dashboard()
                elif choice == '9':
                    self.collaboration_intelligence_dashboard()
                elif choice == '10':
                    self.research_network_analysis()
                else:
                    print(f"{Fore.RED}ERROR: Invalid choice")

                if choice != '0':
                    input(f"\n{Fore.CYAN}Press Enter to continue...")

            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}WARNING: Session interrupted")
                break
            except Exception as e:
                print(f"{Fore.RED}ERROR: {e}")

    def logout(self):
        """Logout admin"""
        self.current_session = None
        self.current_user = None
        print(f"\n{Fore.GREEN}SUCCESS: Logged out successfully")


@click.command()
def main():
    """Admin Interface with Advanced Analytics"""
    cli = AdminCLI()
    cli.run()


if __name__ == "__main__":
    main()