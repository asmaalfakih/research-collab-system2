"""
Research Intelligence Service - Advanced Analytics Queries
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager


class ResearchIntelligenceService:
    """Main service for research intelligence and advanced analytics"""

    @staticmethod
    def get_service_status() -> Dict:
        """Get service status"""
        return {
            'status': 'active',
            'version': '1.0.0',
            'supported_queries': [
                'find_research_bridge',
                'hidden_expert',
                'trust_network',
                'lost_opportunities',
                'high_risk_projects',
                'project_impact',
                'partner_recommendations'
            ]
        }

    # ============= Query 1: Find Research Bridge =============
    @staticmethod
    def find_research_bridge(researcher1_id: str, researcher2_id: str) -> Dict:
        """Find shortest collaboration path between two researchers"""

        researcher1 = mongodb.get_researcher(researcher1_id)
        researcher2 = mongodb.get_researcher(researcher2_id)

        if not researcher1 or not researcher2:
            return {
                'success': False,
                'message': 'One or both researchers not found',
                'data': None
            }

        cache_key = f"research_bridge:{researcher1_id}:{researcher2_id}"

        if redis_manager.is_connected():
            cached = redis_manager.cache_get(cache_key)
            if cached:
                return cached

        try:
            query = """
            MATCH path = shortestPath((r1:Researcher {id: $id1})-[*]-(r2:Researcher {id: $id2}))
            WHERE length(path) > 0
            RETURN 
                nodes(path) as path_nodes,
                relationships(path) as path_rels,
                length(path) as path_length
            ORDER BY path_length
            LIMIT 3
            """

            results = []
            with neo4j.driver.session() as session:
                result = session.run(query, id1=researcher1_id, id2=researcher2_id)

                for record in result:
                    path_nodes = record['path_nodes']
                    path_rels = record['path_rels']
                    path_length = record['path_length']

                    path_details = []
                    for i, node in enumerate(path_nodes):
                        node_type = list(node.labels)[0]

                        if node_type == 'Researcher':
                            researcher_data = mongodb.get_researcher(node['id'])
                            if researcher_data:
                                path_details.append({
                                    'type': 'researcher',
                                    'id': node['id'],
                                    'name': researcher_data.get('name', 'Unknown'),
                                    'department': researcher_data.get('department', 'Unknown'),
                                    'role': 'bridge' if 0 < i < len(path_nodes) - 1 else 'target'
                                })

                    results.append({
                        'path_length': path_length,
                        'path_details': path_details,
                        'total_bridges': max(0, path_length - 1)
                    })

            response = {
                'success': True,
                'message': f'Found {len(results)} possible bridge(s)',
                'data': {
                    'researcher1': {
                        'id': researcher1_id,
                        'name': researcher1.get('name', 'Unknown')
                    },
                    'researcher2': {
                        'id': researcher2_id,
                        'name': researcher2.get('name', 'Unknown')
                    },
                    'bridges': results
                }
            }

            if redis_manager.is_connected():
                redis_manager.cache_set(cache_key, response, ttl_seconds=1800)

            return response

        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }

    # ============= Query 2: Find Hidden Expert =============
    @staticmethod
    def find_hidden_expert(research_area: str, limit: int = 10) -> Dict:
        """Find influential researchers in a specific field despite low publication count"""

        cache_key = f"hidden_expert:{research_area}:{limit}"

        if redis_manager.is_connected():
            cached = redis_manager.cache_get(cache_key)
            if cached:
                return cached

        try:
            researchers = mongodb.db.researchers.find({
                'research_interests': {'$regex': research_area, '$options': 'i'},
                'profile_status': 'approved'
            }).limit(50)

            hidden_experts = []

            for researcher in researchers:
                researcher_id = str(researcher['_id'])

                with neo4j.driver.session() as session:
                    collaboration_stats = session.run("""
                        MATCH (r:Researcher {id: $researcher_id})-[rel:CO_AUTHORED_WITH]-(other:Researcher)
                        RETURN 
                            COUNT(DISTINCT other) as unique_collaborators,
                            AVG(rel.collaboration_count) as avg_collaboration_strength,
                            SUM(rel.collaboration_count) as total_collaborations
                    """, researcher_id=researcher_id)

                    stats = collaboration_stats.single()

                    if stats:
                        publications = mongodb.db.publications.find({
                            'authors.researcher_id': researcher_id
                        })

                        publication_count = 0
                        total_citations = 0

                        for pub in publications:
                            publication_count += 1
                            total_citations += pub.get('citation_count', 0)

                        unique_collaborators = stats['unique_collaborators'] or 0
                        avg_strength = stats['avg_collaboration_strength'] or 0

                        hidden_impact_score = (
                                (unique_collaborators * avg_strength * 0.6) +
                                (total_citations * 0.4)
                        )

                        hidden_experts.append({
                            'id': researcher_id,
                            'name': researcher.get('name', 'Unknown'),
                            'department': researcher.get('department', 'Unknown'),
                            'research_interests': researcher.get('research_interests', []),
                            'unique_collaborators': unique_collaborators,
                            'avg_collaboration_strength': round(avg_strength, 2),
                            'publication_count': publication_count,
                            'total_citations': total_citations,
                            'hidden_impact_score': round(hidden_impact_score, 2)
                        })

            hidden_experts.sort(key=lambda x: x['hidden_impact_score'], reverse=True)

            response = {
                'success': True,
                'message': f'Found {len(hidden_experts)} hidden experts in {research_area}',
                'data': {
                    'research_area': research_area,
                    'experts': hidden_experts[:limit]
                }
            }

            if redis_manager.is_connected():
                redis_manager.cache_set(cache_key, response, ttl_seconds=3600)

            return response

        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }

    # ============= Query 3: Analyze Trust Network =============
    @staticmethod
    def analyze_trust_network(department: str = None, min_collaborations: int = 2) -> Dict:
        """Analyze research trust network in a specific department"""

        cache_key = f"trust_network:{department or 'all'}:{min_collaborations}"

        if redis_manager.is_connected():
            cached = redis_manager.cache_get(cache_key)
            if cached:
                return cached

        try:
            query = """
            MATCH (r1:Researcher)-[rel:CO_AUTHORED_WITH]-(r2:Researcher)
            WHERE rel.collaboration_count >= $min_collaborations
            AND ($department IS NULL OR r1.department = $department OR r2.department = $department)
            RETURN 
                r1.id as researcher1_id,
                r1.name as researcher1_name,
                r1.department as researcher1_dept,
                r2.id as researcher2_id,
                r2.name as researcher2_name,
                r2.department as researcher2_dept,
                rel.collaboration_count as collaboration_count,
                SIZE(rel.publications) as joint_publications
            ORDER BY rel.collaboration_count DESC
            LIMIT 50
            """

            trust_relationships = []
            with neo4j.driver.session() as session:
                result = session.run(
                    query,
                    department=department,
                    min_collaborations=min_collaborations
                )

                for record in result:
                    trust_relationships.append({
                        'researcher1': {
                            'id': record['researcher1_id'],
                            'name': record['researcher1_name'],
                            'department': record['researcher1_dept']
                        },
                        'researcher2': {
                            'id': record['researcher2_id'],
                            'name': record['researcher2_name'],
                            'department': record['researcher2_dept']
                        },
                        'collaboration_count': record['collaboration_count'],
                        'joint_publications': record['joint_publications'],
                        'trust_level': ResearchIntelligenceService._calculate_trust_level(
                            record['collaboration_count'],
                            record['joint_publications']
                        )
                    })

            if trust_relationships:
                total_relationships = len(trust_relationships)
                avg_collaborations = sum(r['collaboration_count'] for r in trust_relationships) / total_relationships

                response = {
                    'success': True,
                    'message': f'Analyzed {total_relationships} trust relationships',
                    'data': {
                        'department': department or 'All Departments',
                        'total_relationships': total_relationships,
                        'avg_collaborations': round(avg_collaborations, 2),
                        'relationships': trust_relationships,
                        'trust_hubs': ResearchIntelligenceService._identify_trust_hubs(trust_relationships),
                        'cross_department_rate': ResearchIntelligenceService._calculate_cross_department_rate(
                            trust_relationships)
                    }
                }
            else:
                response = {
                    'success': True,
                    'message': 'No trust relationships found',
                    'data': None
                }

            if redis_manager.is_connected():
                redis_manager.cache_set(cache_key, response, ttl_seconds=2700)

            return response

        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }

    # ============= Query 4: Find Lost Opportunities =============
    @staticmethod
    def find_lost_opportunities(min_similarity: float = 0.5) -> Dict:
        """Find missed collaboration opportunities between similar researchers"""

        cache_key = f"lost_opportunities:{min_similarity}"

        if redis_manager.is_connected():
            cached = redis_manager.cache_get(cache_key)
            if cached:
                return cached

        try:
            all_researchers = list(mongodb.db.researchers.find({
                'profile_status': 'approved'
            }, {'name': 1, 'email': 1, 'department': 1, 'research_interests': 1}))

            lost_opportunities = []

            for i, r1 in enumerate(all_researchers):
                for j, r2 in enumerate(all_researchers):
                    if i >= j:
                        continue

                    r1_id = str(r1['_id'])
                    r2_id = str(r2['_id'])

                    with neo4j.driver.session() as session:
                        existing_collab = session.run("""
                            MATCH (r1:Researcher {id: $id1})-[rel:CO_AUTHORED_WITH]-(r2:Researcher {id: $id2})
                            RETURN COUNT(rel) as collaboration_count
                        """, id1=r1_id, id2=r2_id)

                        collab_count = existing_collab.single()['collaboration_count']

                        if collab_count == 0:
                            interests1 = set(r1.get('research_interests', []))
                            interests2 = set(r2.get('research_interests', []))

                            if interests1 and interests2:
                                common_interests = interests1.intersection(interests2)
                                similarity = len(common_interests) / max(len(interests1), len(interests2))

                                if similarity >= min_similarity:
                                    lost_opportunities.append({
                                        'researcher1': {
                                            'id': r1_id,
                                            'name': r1.get('name', 'Unknown'),
                                            'department': r1.get('department', 'Unknown')
                                        },
                                        'researcher2': {
                                            'id': r2_id,
                                            'name': r2.get('name', 'Unknown'),
                                            'department': r2.get('department', 'Unknown')
                                        },
                                        'similarity_percentage': round(similarity * 100, 2),
                                        'common_interests': list(common_interests),
                                        'opportunity_score': round(similarity * 100, 2)
                                    })

            lost_opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)

            response = {
                'success': True,
                'message': f'Found {len(lost_opportunities)} lost collaboration opportunities',
                'data': {
                    'min_similarity': f'{min_similarity * 100}%',
                    'opportunities': lost_opportunities[:20]
                }
            }

            if redis_manager.is_connected():
                redis_manager.cache_set(cache_key, response, ttl_seconds=3600)

            return response

        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }

    # ============= Query 5: Identify High-Risk Projects =============
    @staticmethod
    def identify_high_risk_projects(risk_threshold: float = 1.5) -> Dict:
        """Identify projects with diverse teams but little prior collaboration"""

        cache_key = f"high_risk_projects:{risk_threshold}"

        if redis_manager.is_connected():
            cached = redis_manager.cache_get(cache_key)
            if cached:
                return cached

        try:
            high_risk_projects = []

            projects = mongodb.db.projects.find({
                'status': 'active'
            }).limit(50)

            for project in projects:
                project_id = str(project['_id'])
                participants = project.get('participants', [])

                if len(participants) >= 3:
                    departments = set()
                    prior_collaborations = 0
                    total_possible_collaborations = 0

                    for i in range(len(participants)):
                        for j in range(i + 1, len(participants)):
                            total_possible_collaborations += 1

                            r1 = mongodb.get_researcher(participants[i])
                            r2 = mongodb.get_researcher(participants[j])

                            if r1 and r2:
                                departments.add(r1.get('department', 'Unknown'))
                                departments.add(r2.get('department', 'Unknown'))

                                with neo4j.driver.session() as session:
                                    prior_collab = session.run("""
                                        MATCH (r1:Researcher {id: $id1})-[rel:CO_AUTHORED_WITH]-(r2:Researcher {id: $id2})
                                        RETURN COUNT(rel) as collaboration_count
                                    """, id1=participants[i], id2=participants[j])

                                    collab_count = prior_collab.single()['collaboration_count'] or 0
                                    if collab_count > 0:
                                        prior_collaborations += 1

                    if total_possible_collaborations > 0:
                        department_diversity = len(departments)
                        collaboration_rate = prior_collaborations / total_possible_collaborations

                        risk_score = (department_diversity * 0.7) - (collaboration_rate * 0.3)

                        if risk_score >= risk_threshold:
                            high_risk_projects.append({
                                'project_id': project_id,
                                'title': project.get('title', 'Unknown'),
                                'team_size': len(participants),
                                'department_diversity': department_diversity,
                                'collaboration_rate': round(collaboration_rate * 100, 2),
                                'risk_score': round(risk_score, 2),
                                'risk_level': ResearchIntelligenceService._get_risk_level(risk_score)
                            })

            high_risk_projects.sort(key=lambda x: x['risk_score'], reverse=True)

            response = {
                'success': True,
                'message': f'Found {len(high_risk_projects)} high-risk projects',
                'data': {
                    'risk_threshold': risk_threshold,
                    'projects': high_risk_projects[:15]
                }
            }

            if redis_manager.is_connected():
                redis_manager.cache_set(cache_key, response, ttl_seconds=3000)

            return response

        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }

    # ============= Query 6: Analyze Project Research Impact =============
    @staticmethod
    def analyze_project_research_impact(project_id: str) -> Dict:
        """Analyze how project affected participant research output"""

        cache_key = f"project_impact:{project_id}"

        if redis_manager.is_connected():
            cached = redis_manager.cache_get(cache_key)
            if cached:
                return cached

        try:
            project = mongodb.get_project(project_id)
            if not project:
                return {
                    'success': False,
                    'message': 'Project not found',
                    'data': None
                }

            start_date = project.get('start_date')
            if not start_date:
                return {
                    'success': False,
                    'message': 'Project start date not found',
                    'data': None
                }

            impact_analysis = {
                'project_info': {
                    'title': project.get('title'),
                    'start_date': start_date,
                    'team_size': len(project.get('participants', []))
                },
                'participant_impact': []
            }

            for participant_id in project.get('participants', []):
                participant = mongodb.get_researcher(participant_id)
                if participant:
                    participant_name = participant.get('name', 'Unknown')

                    publications = mongodb.db.publications.find({
                        'authors.researcher_id': participant_id
                    })

                    publications_before = 0
                    publications_after = 0
                    citations_before = 0
                    citations_after = 0

                    for pub in publications:
                        pub_year = pub.get('year', 0)
                        citation_count = pub.get('citation_count', 0)

                        if pub_year < int(start_date[:4]):
                            publications_before += 1
                            citations_before += citation_count
                        else:
                            publications_after += 1
                            citations_after += citation_count

                    growth_percentage = 0
                    if publications_before > 0:
                        growth_percentage = ((publications_after - publications_before) / publications_before) * 100

                    impact_analysis['participant_impact'].append({
                        'researcher_id': participant_id,
                        'researcher_name': participant_name,
                        'publications_before': publications_before,
                        'publications_after': publications_after,
                        'publication_growth': round(growth_percentage, 2),
                        'citations_before': citations_before,
                        'citations_after': citations_after,
                        'impact_level': 'High' if growth_percentage > 50 else 'Medium' if growth_percentage > 10 else 'Low'
                    })

            response = {
                'success': True,
                'message': f'Analyzed impact for {len(impact_analysis["participant_impact"])} participants',
                'data': impact_analysis
            }

            if redis_manager.is_connected():
                redis_manager.cache_set(cache_key, response, ttl_seconds=3600)

            return response

        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }

    # ============= Query 7: Recommend Research Partners =============
    @staticmethod
    def recommend_research_partners(researcher_id: str, limit: int = 5) -> Dict:
        """Recommend research partners based on multiple criteria"""

        cache_key = f"partner_recommendations:{researcher_id}:{limit}"

        if redis_manager.is_connected():
            cached = redis_manager.cache_get(cache_key)
            if cached:
                return cached

        try:
            target_researcher = mongodb.get_researcher(researcher_id)
            if not target_researcher:
                return {
                    'success': False,
                    'message': 'Researcher not found',
                    'data': None
                }

            target_interests = set(target_researcher.get('research_interests', []))

            recommendations = []

            all_researchers = list(mongodb.db.researchers.find({
                '_id': {'$ne': ObjectId(researcher_id)},
                'profile_status': 'approved'
            }, {'name': 1, 'department': 1, 'research_interests': 1}).limit(100))

            for candidate in all_researchers:
                candidate_id = str(candidate['_id'])

                if candidate_id == researcher_id:
                    continue

                candidate_interests = set(candidate.get('research_interests', []))

                common_interests = target_interests.intersection(candidate_interests)
                complementary_interests = target_interests.difference(candidate_interests)

                interest_similarity = len(common_interests) / max(len(target_interests),
                                                                  len(candidate_interests)) if target_interests and candidate_interests else 0

                with neo4j.driver.session() as session:
                    mutual_connections = session.run("""
                        MATCH (r1:Researcher {id: $id1})-[rel1:CO_AUTHORED_WITH]-(mutual:Researcher)-[rel2:CO_AUTHORED_WITH]-(r2:Researcher {id: $id2})
                        RETURN COUNT(DISTINCT mutual) as mutual_count
                    """, id1=researcher_id, id2=candidate_id)

                    mutual_count = mutual_connections.single()['mutual_count'] or 0

                recommendation_score = (
                        (interest_similarity * 0.4) +
                        (mutual_count * 0.3) +
                        (len(complementary_interests) * 0.3)
                )

                recommendations.append({
                    'candidate_id': candidate_id,
                    'candidate_name': candidate.get('name', 'Unknown'),
                    'candidate_department': candidate.get('department', 'Unknown'),
                    'common_interests': list(common_interests),
                    'complementary_interests': list(complementary_interests),
                    'mutual_connections': mutual_count,
                    'recommendation_score': round(recommendation_score, 3),
                    'recommendation_level': 'High' if recommendation_score > 0.7 else 'Medium' if recommendation_score > 0.4 else 'Low'
                })

            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)

            response = {
                'success': True,
                'message': f'Found {len(recommendations)} potential partners',
                'data': {
                    'target_researcher': {
                        'id': researcher_id,
                        'name': target_researcher.get('name', 'Unknown')
                    },
                    'recommendations': recommendations[:limit]
                }
            }

            if redis_manager.is_connected():
                redis_manager.cache_set(cache_key, response, ttl_seconds=2400)

            return response

        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }

    # ============= Helper Methods =============
    @staticmethod
    def _calculate_trust_level(collaboration_count: int, joint_publications: int) -> str:
        score = (collaboration_count * 0.6) + (joint_publications * 0.4)

        if score >= 10:
            return "Very High"
        elif score >= 5:
            return "High"
        elif score >= 2:
            return "Medium"
        else:
            return "Low"

    @staticmethod
    def _identify_trust_hubs(relationships: List[Dict]) -> List[Dict]:
        researcher_scores = {}

        for rel in relationships:
            r1_id = rel['researcher1']['id']
            r2_id = rel['researcher2']['id']

            researcher_scores[r1_id] = researcher_scores.get(r1_id, 0) + rel['collaboration_count']
            researcher_scores[r2_id] = researcher_scores.get(r2_id, 0) + rel['collaboration_count']

        sorted_researchers = sorted(researcher_scores.items(), key=lambda x: x[1], reverse=True)

        hubs = []
        for researcher_id, score in sorted_researchers[:5]:
            researcher = mongodb.get_researcher(researcher_id)
            if researcher:
                hubs.append({
                    'id': researcher_id,
                    'name': researcher.get('name', 'Unknown'),
                    'department': researcher.get('department', 'Unknown'),
                    'trust_score': score
                })

        return hubs

    @staticmethod
    def _calculate_cross_department_rate(relationships: List[Dict]) -> float:
        if not relationships:
            return 0.0

        cross_dept_count = 0

        for rel in relationships:
            if rel['researcher1']['department'] != rel['researcher2']['department']:
                cross_dept_count += 1

        return round((cross_dept_count / len(relationships)) * 100, 2)

    @staticmethod
    def _get_risk_level(risk_score: float) -> str:
        if risk_score >= 2.5:
            return "Very High"
        elif risk_score >= 1.8:
            return "High"
        elif risk_score >= 1.0:
            return "Medium"
        else:
            return "Low"