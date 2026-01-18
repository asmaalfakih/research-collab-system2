from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional, Tuple
from .connection import DatabaseConfig
from colorama import Fore, Style


class Neo4jManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_neo4j()
        return cls._instance

    def _init_neo4j(self):
        config = DatabaseConfig.get_neo4j_config()
        try:
            self.driver = GraphDatabase.driver(
                config['uri'],
                auth=(config['username'], config['password']),
                connection_timeout=10
            )
            with self.driver.session() as session:
                session.run("RETURN 1")
                self._setup_constraints()
            print(f"{Fore.GREEN}PASS: Neo4j connected successfully")
        except Exception as e:
            print(f"{Fore.RED}FAIL: Neo4j connection failed: {e}")
            self.driver = None

    def _setup_constraints(self):
        constraints = [
            "CREATE CONSTRAINT researcher_id_unique IF NOT EXISTS FOR (r:Researcher) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT publication_id_unique IF NOT EXISTS FOR (pub:Publication) REQUIRE pub.id IS UNIQUE"
        ]
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"{Fore.YELLOW}WARN: Could not create constraint: {e}")

    def create_researcher_node(self, researcher_data: Dict) -> bool:
        query = """
        MERGE (r:Researcher {id: $id})
        SET r.name = $name,
            r.email = $email,
            r.department = $department,
            r.profile_status = $profile_status,
            r.created_at = datetime()
        RETURN r
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, **researcher_data)
                return result.single() is not None
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating researcher node: {e}")
            return False

    def create_project_node(self, project_data: Dict) -> bool:
        query = """
        MERGE (p:Project {id: $id})
        SET p.title = $title,
            p.creator_id = $creator_id,
            p.status = $status,
            p.created_at = datetime()
        RETURN p
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, **project_data)
                return result.single() is not None
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating project node: {e}")
            return False

    def create_publication_node(self, publication_data: Dict) -> bool:
        query = """
        MERGE (pub:Publication {id: $id})
        SET pub.title = $title,
            pub.year = $year,
            pub.created_at = datetime()
        RETURN pub
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, **publication_data)
                return result.single() is not None
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating publication node: {e}")
            return False

    def create_coauthorship(self, researcher1_id: str, researcher2_id: str, publication_id: str = None) -> int:
        query = """
        MATCH (r1:Researcher {id: $researcher1_id})
        MATCH (r2:Researcher {id: $researcher2_id})
        MERGE (r1)-[rel:CO_AUTHORED_WITH]-(r2)
        ON CREATE SET 
            rel.collaboration_count = 1,
            rel.first_collaboration = date(),
            rel.last_collaboration = date(),
            rel.publications = CASE WHEN $publication_id IS NOT NULL THEN [$publication_id] ELSE [] END,
            rel.relationship_id = $relationship_id,
            rel.created_at = datetime()
        ON MATCH SET 
            rel.collaboration_count = rel.collaboration_count + 1,
            rel.last_collaboration = date(),
            rel.updated_at = datetime(),
            rel.publications = CASE WHEN $publication_id IS NOT NULL AND NOT $publication_id IN rel.publications 
                                 THEN rel.publications + $publication_id 
                                 ELSE rel.publications END
        RETURN rel.collaboration_count AS new_count
        """
        relationship_id = f"{researcher1_id}-{researcher2_id}-{uuid.uuid4().hex[:8]}"
        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    researcher1_id=researcher1_id,
                    researcher2_id=researcher2_id,
                    publication_id=publication_id,
                    relationship_id=relationship_id
                )
                record = result.single()
                return record["new_count"] if record else 0
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating coauthorship: {e}")
            return 0

    def create_supervision(self, supervisor_id: str, student_id: str, project_id: str = None) -> int:
        query = """
        MATCH (supervisor:Researcher {id: $supervisor_id})
        MATCH (student:Researcher {id: $student_id})
        MERGE (supervisor)-[rel:SUPERVISED]->(student)
        ON CREATE SET 
            rel.collaboration_count = 1,
            rel.start_date = date(),
            rel.projects = CASE WHEN $project_id IS NOT NULL THEN [$project_id] ELSE [] END,
            rel.created_at = datetime()
        ON MATCH SET 
            rel.collaboration_count = rel.collaboration_count + 1,
            rel.updated_at = datetime(),
            rel.projects = CASE WHEN $project_id IS NOT NULL AND NOT $project_id IN rel.projects 
                             THEN rel.projects + $project_id 
                             ELSE rel.projects END
        RETURN rel.collaboration_count AS new_count
        """
        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    supervisor_id=supervisor_id,
                    student_id=student_id,
                    project_id=project_id
                )
                record = result.single()
                return record["new_count"] if record else 0
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating supervision: {e}")
            return 0

    def create_teamwork(self, researcher1_id: str, researcher2_id: str, project_id: str = None) -> int:
        query = """
        MATCH (r1:Researcher {id: $researcher1_id})
        MATCH (r2:Researcher {id: $researcher2_id})
        MERGE (r1)-[rel:TEAMWORK_WITH]-(r2)
        ON CREATE SET 
            rel.collaboration_count = 1,
            rel.first_collaboration = date(),
            rel.last_collaboration = date(),
            rel.projects = CASE WHEN $project_id IS NOT NULL THEN [$project_id] ELSE [] END,
            rel.relationship_id = $relationship_id,
            rel.created_at = datetime()
        ON MATCH SET 
            rel.collaboration_count = rel.collaboration_count + 1,
            rel.last_collaboration = date(),
            rel.updated_at = datetime(),
            rel.projects = CASE WHEN $project_id IS NOT NULL AND NOT $project_id IN rel.projects 
                             THEN rel.projects + $project_id 
                             ELSE rel.projects END
        RETURN rel.collaboration_count AS new_count
        """
        relationship_id = f"{researcher1_id}-{researcher2_id}-{uuid.uuid4().hex[:8]}"
        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    researcher1_id=researcher1_id,
                    researcher2_id=researcher2_id,
                    project_id=project_id,
                    relationship_id=relationship_id
                )
                record = result.single()
                return record["new_count"] if record else 0
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating teamwork: {e}")
            return 0

    def create_project_participation(self, researcher_id: str, project_id: str) -> bool:
        query = """
        MATCH (r:Researcher {id: $researcher_id})
        MATCH (p:Project {id: $project_id})
        MERGE (r)-[rel:PARTICIPATED_IN]->(p)
        ON CREATE SET 
            rel.joined_date = date(),
            rel.relationship_id = $relationship_id
        RETURN rel
        """
        relationship_id = f"{researcher_id}-{project_id}-{uuid.uuid4().hex[:8]}"
        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    researcher_id=researcher_id,
                    project_id=project_id,
                    relationship_id=relationship_id
                )
                return result.single() is not None
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating project participation: {e}")
            return False

    def create_authorship(self, researcher_id: str, publication_id: str, author_order: int = 1) -> bool:
        query = """
        MATCH (r:Researcher {id: $researcher_id})
        MATCH (pub:Publication {id: $publication_id})
        MERGE (r)-[rel:AUTHORED]->(pub)
        ON CREATE SET 
            rel.author_order = $author_order,
            rel.created_at = datetime()
        RETURN rel
        """
        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    researcher_id=researcher_id,
                    publication_id=publication_id,
                    author_order=author_order
                )
                return result.single() is not None
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating authorship: {e}")
            return False

    def create_produced_relationship(self, project_id: str, publication_id: str) -> bool:
        query = """
        MATCH (p:Project {id: $project_id})
        MATCH (pub:Publication {id: $publication_id})
        MERGE (p)-[rel:PRODUCED]->(pub)
        ON CREATE SET 
            rel.created_at = datetime()
        RETURN rel
        """
        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    project_id=project_id,
                    publication_id=publication_id
                )
                return result.single() is not None
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error creating produced relationship: {e}")
            return False

    def get_all_relationships(self) -> List[Dict]:
        query = """
        MATCH (r1:Researcher)-[rel]-(r2:Researcher)
        WHERE r1.id < r2.id
        RETURN 
            r1.id AS researcher1_id,
            r1.name AS researcher1_name,
            r2.id AS researcher2_id,
            r2.name AS researcher2_name,
            type(rel) AS relationship_type,
            rel.collaboration_count AS collaboration_count,
            rel.first_collaboration AS first_collaboration,
            rel.last_collaboration AS last_collaboration
        ORDER BY rel.collaboration_count DESC
        """
        try:
            with self.driver.session() as session:
                result = session.run(query)
                relationships = []
                for record in result:
                    relationships.append({
                        'researcher1_id': record['researcher1_id'],
                        'researcher1_name': record['researcher1_name'],
                        'researcher2_id': record['researcher2_id'],
                        'researcher2_name': record['researcher2_name'],
                        'relationship_type': record['relationship_type'],
                        'collaboration_count': record['collaboration_count'],
                        'first_collaboration': record['first_collaboration'],
                        'last_collaboration': record['last_collaboration']
                    })
                return relationships
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error getting relationships: {e}")
            return []

    def get_relationships_by_type(self, relationship_type: str) -> List[Dict]:
        query = f"""
        MATCH (r1:Researcher)-[rel:{relationship_type}]-(r2:Researcher)
        WHERE r1.id < r2.id
        RETURN 
            r1.id AS researcher1_id,
            r1.name AS researcher1_name,
            r2.id AS researcher2_id,
            r2.name AS researcher2_name,
            rel.collaboration_count AS collaboration_count
        ORDER BY rel.collaboration_count DESC
        """
        try:
            with self.driver.session() as session:
                result = session.run(query)
                relationships = []
                for record in result:
                    relationships.append({
                        'researcher1_id': record['researcher1_id'],
                        'researcher1_name': record['researcher1_name'],
                        'researcher2_id': record['researcher2_id'],
                        'researcher2_name': record['researcher2_name'],
                        'collaboration_count': record['collaboration_count']
                    })
                return relationships
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error getting relationships by type: {e}")
            return []

    def get_researcher_relationships(self, researcher_id: str) -> List[Dict]:
        query = """
        MATCH (r:Researcher {id: $researcher_id})-[rel]-(other:Researcher)
        RETURN 
            other.id AS other_id,
            other.name AS other_name,
            type(rel) AS relationship_type,
            rel.collaboration_count AS collaboration_count
        ORDER BY rel.collaboration_count DESC
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, researcher_id=researcher_id)
                relationships = []
                for record in result:
                    relationships.append({
                        'other_id': record['other_id'],
                        'other_name': record['other_name'],
                        'relationship_type': record['relationship_type'],
                        'collaboration_count': record['collaboration_count']
                    })
                return relationships
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error getting researcher relationships: {e}")
            return []

    def get_relationship_stats(self) -> Dict:
        queries = {
            'total_coauthorships': "MATCH ()-[r:CO_AUTHORED_WITH]-() RETURN count(r) AS count",
            'total_supervisions': "MATCH ()-[r:SUPERVISED]-() RETURN count(r) AS count",
            'total_teamworks': "MATCH ()-[r:TEAMWORK_WITH]-() RETURN count(r) AS count",
            'most_active_coauthorship': """
                MATCH ()-[r:CO_AUTHORED_WITH]-()
                RETURN r.collaboration_count AS count
                ORDER BY r.collaboration_count DESC
                LIMIT 1
            """,
            'most_active_supervision': """
                MATCH ()-[r:SUPERVISED]-()
                RETURN r.collaboration_count AS count
                ORDER BY r.collaboration_count DESC
                LIMIT 1
            """,
            'most_active_teamwork': """
                MATCH ()-[r:TEAMWORK_WITH]-()
                RETURN r.collaboration_count AS count
                ORDER BY r.collaboration_count DESC
                LIMIT 1
            """
        }
        stats = {}
        try:
            with self.driver.session() as session:
                for stat_name, query in queries.items():
                    result = session.run(query)
                    record = result.single()
                    if record:
                        stats[stat_name] = record[0] if len(record) > 0 else None
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error getting relationship stats: {e}")
        return stats

    # === الدوال الجديدة المطلوبة ===

    def get_relationship_counts(self) -> Dict[str, int]:
        """Get counts for all 6 relationship types"""
        query = """
        MATCH ()-[r]-()
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY rel_type
        """
        counts = {}
        try:
            with self.driver.session() as session:
                result = session.run(query)
                for record in result:
                    counts[record["rel_type"]] = record["count"]
        except Exception as e:
            print(f"Error getting relationship counts: {e}")
        return counts

    def get_relationship_count_by_type(self, relationship_type: str) -> int:
        """Get count for specific relationship type"""
        query = f"""
        MATCH ()-[r:{relationship_type}]-()
        RETURN count(r) as count
        """
        try:
            with self.driver.session() as session:
                result = session.run(query)
                record = result.single()
                return record["count"] if record else 0
        except Exception as e:
            print(f"Error getting count for {relationship_type}: {e}")
            return 0

    def delete_coauthorship(self, researcher1_id: str, researcher2_id: str) -> bool:
        """Delete coauthorship relationship"""
        query = """
        MATCH (r1:Researcher {id: $id1})-[rel:CO_AUTHORED_WITH]-(r2:Researcher {id: $id2})
        DELETE rel
        RETURN count(rel) as deleted
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, id1=researcher1_id, id2=researcher2_id)
                record = result.single()
                return record["deleted"] > 0 if record else False
        except Exception as e:
            print(f"Error deleting coauthorship: {e}")
            return False

    def delete_supervision(self, supervisor_id: str, student_id: str) -> bool:
        """Delete supervision relationship"""
        query = """
        MATCH (supervisor:Researcher {id: $supervisor_id})-[rel:SUPERVISED]->(student:Researcher {id: $student_id})
        DELETE rel
        RETURN count(rel) as deleted
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, supervisor_id=supervisor_id, student_id=student_id)
                record = result.single()
                return record["deleted"] > 0 if record else False
        except Exception as e:
            print(f"Error deleting supervision: {e}")
            return False

    def delete_teamwork(self, researcher1_id: str, researcher2_id: str) -> bool:
        """Delete teamwork relationship"""
        query = """
        MATCH (r1:Researcher {id: $id1})-[rel:TEAMWORK_WITH]-(r2:Researcher {id: $id2})
        DELETE rel
        RETURN count(rel) as deleted
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, id1=researcher1_id, id2=researcher2_id)
                record = result.single()
                return record["deleted"] > 0 if record else False
        except Exception as e:
            print(f"Error deleting teamwork: {e}")
            return False

    def delete_participation(self, researcher_id: str, project_id: str) -> bool:
        """Delete participation relationship"""
        query = """
        MATCH (r:Researcher {id: $researcher_id})-[rel:PARTICIPATED_IN]->(p:Project {id: $project_id})
        DELETE rel
        RETURN count(rel) as deleted
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, researcher_id=researcher_id, project_id=project_id)
                record = result.single()
                return record["deleted"] > 0 if record else False
        except Exception as e:
            print(f"Error deleting participation: {e}")
            return False

    def delete_authorship(self, researcher_id: str, publication_id: str) -> bool:
        """Delete authorship relationship"""
        query = """
        MATCH (r:Researcher {id: $researcher_id})-[rel:AUTHORED]->(pub:Publication {id: $publication_id})
        DELETE rel
        RETURN count(rel) as deleted
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, researcher_id=researcher_id, publication_id=publication_id)
                record = result.single()
                return record["deleted"] > 0 if record else False
        except Exception as e:
            print(f"Error deleting authorship: {e}")
            return False

    def delete_produced_relationship(self, project_id: str, publication_id: str) -> bool:
        """Delete produced relationship"""
        query = """
        MATCH (p:Project {id: $project_id})-[rel:PRODUCED]->(pub:Publication {id: $publication_id})
        DELETE rel
        RETURN count(rel) as deleted
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, project_id=project_id, publication_id=publication_id)
                record = result.single()
                return record["deleted"] > 0 if record else False
        except Exception as e:
            print(f"Error deleting produced relationship: {e}")
            return False

    def get_researcher_collaborators(self, researcher_id: str) -> List[Dict]:
        query = """
        MATCH (r:Researcher {id: $researcher_id})-[rel]-(other:Researcher)
        RETURN 
            other.id AS collaborator_id,
            other.name AS collaborator_name,
            other.department AS department,
            type(rel) AS collaboration_type,
            rel.collaboration_count AS collaboration_count
        ORDER BY rel.collaboration_count DESC
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, researcher_id=researcher_id)
                collaborators = []
                for record in result:
                    collaborators.append({
                        'collaborator_id': record['collaborator_id'],
                        'collaborator_name': record['collaborator_name'],
                        'department': record['department'],
                        'collaboration_type': record['collaboration_type'],
                        'collaboration_count': record['collaboration_count']
                    })
                return collaborators
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error getting researcher collaborators: {e}")
            return []

    def get_researcher_network(self, researcher_id: str, depth: int = 2) -> Dict:
        query = """
        MATCH (r:Researcher {id: $researcher_id})
        OPTIONAL MATCH (r)-[rel*1..$depth]-(other:Researcher)
        RETURN r, collect(DISTINCT other) as connections
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, researcher_id=researcher_id, depth=depth)
                record = result.single()
                if record:
                    return {
                        'central_researcher': dict(record['r']),
                        'connections': [dict(node) for node in record['connections']]
                    }
                return None
        except Neo4jError as e:
            print(f"{Fore.RED}FAIL: Error getting researcher network: {e}")
            return None

    def close(self):
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")


neo4j = Neo4jManager()