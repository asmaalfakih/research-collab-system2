#!/usr/bin/env python3
"""Create sample researchers for testing"""

from app.database.mongodb import mongodb
from app.models.researcher import Researcher
from app.database.neo4j import neo4j

print("Creating sample researchers...")

# First researcher
researcher1_data = {
    'name': 'Dr. Test Researcher 1',
    'email': 'test.researcher1@university.edu',
    'password': Researcher.hash_password('test123'),
    'department': 'Computer Science',
    'profile_status': 'approved',
    'role': 'researcher',
    'research_interests': ['AI', 'Machine Learning']
}

# Second researcher
researcher2_data = {
    'name': 'Dr. Test Researcher 2',
    'email': 'test.researcher2@university.edu',
    'password': Researcher.hash_password('test123'),
    'department': 'Information Technology',
    'profile_status': 'approved',
    'role': 'researcher',
    'research_interests': ['Networks', 'Security']
}

# Create in MongoDB
researcher1_id = mongodb.create_researcher(researcher1_data)
researcher2_id = mongodb.create_researcher(researcher2_data)

print(f"Created researcher 1: {researcher1_id}")
print(f"Created researcher 2: {researcher2_id}")

# Create in Neo4j
neo4j.create_researcher_node({
    'id': researcher1_id,
    'name': researcher1_data['name'],
    'email': researcher1_data['email'],
    'department': researcher1_data['department'],
    'profile_status': researcher1_data['profile_status']
})

neo4j.create_researcher_node({
    'id': researcher2_id,
    'name': researcher2_data['name'],
    'email': researcher2_data['email'],
    'department': researcher2_data['department'],
    'profile_status': researcher2_data['profile_status']
})

print("Researchers created in Neo4j")

# Create collaboration relationship between them
count = neo4j.create_or_update_collaboration(
    researcher1_id,
    researcher2_id,
    "project"
)

print(f"Collaboration created. Count: {count}")

# Test relationship
collaborators = neo4j.get_researcher_collaborators(researcher1_id)
print(f"Collaborators for researcher 1: {len(collaborators)}")

print("\nTest researchers setup complete!")
print(f"Researcher 1: {researcher1_data['email']}")
print(f"Researcher 2: {researcher2_data['email']}")
print(f"Password for both: test123")