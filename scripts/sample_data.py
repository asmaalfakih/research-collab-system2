#!/usr/bin/env python3
"""
Create large sample data for testing
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import bcrypt
import random
import string
import time
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent))

from colorama import init, Fore, Style

init(autoreset=True)

fake = Faker()


def get_utc_now():
    return datetime.utcnow()


def generate_random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


def generate_researcher_data(count=100):
    departments = [
        'Computer Science', 'Information Technology', 'Data Science',
        'Software Engineering', 'Cybersecurity', 'Artificial Intelligence',
        'Networks', 'Bioinformatics', 'Computer Engineering'
    ]

    research_interests_pool = [
        'Machine Learning', 'Deep Learning', 'Natural Language Processing',
        'Computer Vision', 'Big Data', 'Cloud Computing', 'IoT',
        'Blockchain', 'Quantum Computing', 'Robotics', 'Data Mining',
        'Web Development', 'Mobile Applications', 'Game Development',
        'Database Systems', 'Information Security', 'Network Security',
        'Bioinformatics', 'Health Informatics', 'Educational Technology'
    ]

    researchers = []
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        name = f"Dr. {first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}@university.edu"

        interests = random.sample(research_interests_pool, random.randint(2, 5))

        researcher = {
            'name': name,
            'email': email,
            'password': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'department': random.choice(departments),
            'profile_status': 'approved',
            'role': 'researcher',
            'research_interests': interests,
            'contact': {
                'phone': f'0599{random.randint(100000, 999999)}',
                'city': random.choice(['Hebron', 'Ramallah', 'Bethlehem', 'Nablus', 'Jerusalem', 'Gaza'])
            },
            'created_at': get_utc_now() - timedelta(days=random.randint(1, 365)),
            'last_login': get_utc_now() - timedelta(days=random.randint(0, 30))
        }
        researchers.append(researcher)

    return researchers


def generate_project_data(count=50, researcher_ids=[]):
    project_titles = [
        'AI in Healthcare', 'Smart City Solutions', 'Renewable Energy Systems',
        'Cybersecurity Framework', 'Big Data Analytics', 'IoT for Agriculture',
        'Blockchain Applications', 'Virtual Reality in Education',
        'Machine Learning Models', 'Cloud Computing Infrastructure',
        'Mobile Health Applications', 'Automated Testing Systems',
        'Natural Language Processing Tools', 'Computer Vision Systems',
        'Data Privacy Solutions', 'Network Optimization',
        'Software Development Methodologies', 'Database Management Systems',
        'Web Application Security', 'Predictive Analytics'
    ]

    research_areas = [
        'Artificial Intelligence', 'Software Engineering', 'Data Science',
        'Cybersecurity', 'Networks', 'Cloud Computing', 'IoT',
        'Mobile Computing', 'Web Technologies', 'Database Systems'
    ]

    funding_sources = [
        'University Research Grant', 'Ministry of Education',
        'International Research Council', 'Private Sector Partnership',
        'EU Research Fund', 'National Science Foundation'
    ]

    projects = []
    for i in range(count):
        title = f"{random.choice(project_titles)} - Phase {random.randint(1, 3)}"

        participants = random.sample(researcher_ids, random.randint(2, min(5, len(researcher_ids))))
        creator_id = participants[0]

        start_date = get_utc_now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(90, 720))

        project = {
            'title': title,
            'description': fake.text(max_nb_chars=200),
            'creator_id': creator_id,
            'creator_name': f"Researcher {creator_id[:8]}",
            'participants': participants,
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat(),
            'status': random.choice(['active', 'completed', 'pending']),
            'research_area': random.choice(research_areas),
            'tags': random.sample(['AI', 'ML', 'Data', 'Cloud', 'Security'], random.randint(2, 4)),
            'budget': random.uniform(10000, 100000),
            'funding_source': random.choice(funding_sources),
            'created_at': start_date,
            'updated_at': get_utc_now(),
            'milestones': [
                {
                    'title': f'Milestone {j + 1}',
                    'description': f'Project milestone {j + 1}',
                    'due_date': (start_date + timedelta(days=30 * (j + 1))).date().isoformat(),
                    'completed': j < random.randint(1, 3)
                }
                for j in range(random.randint(3, 6))
            ]
        }
        projects.append(project)

    return projects


def generate_publication_data(count=30, researcher_ids=[]):
    journals = [
        'Journal of Computer Science', 'IEEE Transactions',
        'ACM Computing Surveys', 'Science Direct',
        'Springer Nature', 'Elsevier', 'Wiley'
    ]

    keywords_pool = [
        'machine learning', 'deep learning', 'artificial intelligence',
        'data mining', 'cloud computing', 'cybersecurity',
        'internet of things', 'big data', 'blockchain',
        'natural language processing', 'computer vision'
    ]

    publications = []
    for i in range(count):
        title = fake.sentence(nb_words=8, variable_nb_words=True)

        num_authors = random.randint(1, min(6, len(researcher_ids)))
        authors = random.sample(researcher_ids, num_authors)

        publication = {
            'title': title,
            'authors': [
                {
                    'researcher_id': author_id,
                    'name': f"Researcher {author_id[:8]}",
                    'order': j + 1,
                    'affiliation': 'Palestine Polytechnic University',
                    'contribution': random.choice(['Main researcher', 'Data analysis', 'Writing', 'Experiments'])
                }
                for j, author_id in enumerate(authors)
            ],
            'year': random.randint(2018, 2024),
            'doi': f"10.1000/{int(time.time() * 1000)}_{i}_{random.randint(1000, 9999)}",
            'journal': random.choice(journals),
            'abstract': fake.text(max_nb_chars=300),
            'keywords': random.sample(keywords_pool, random.randint(3, 6)),
            'citation_count': random.randint(0, 100),
            'status': 'published',
            'views': random.randint(50, 1000),
            'downloads': random.randint(10, 500),
            'created_at': get_utc_now() - timedelta(days=random.randint(1, 365)),
            'updated_at': get_utc_now()
        }
        publications.append(publication)

    return publications


def create_diverse_relationships(researcher_ids, project_ids, publication_ids):
    relationships_created = {
        'SUPERVISED': 0,
        'AUTHORED': 0,
        'PRODUCED': 0,
        'CO_AUTHORED_WITH': 0,
        'TEAMWORK_WITH': 0,
        'PARTICIPATED_IN': 0
    }

    for _ in range(min(30, len(researcher_ids))):  # 30 علاقة إشراف
        supervisor_id = random.choice(researcher_ids)
        student_id = random.choice(researcher_ids)
        if supervisor_id != student_id:
            if neo4j.create_supervision(supervisor_id, student_id):
                relationships_created['SUPERVISED'] += 1

    # علاقات المشاركة في المشاريع (PARTICIPATED_IN) - باحث يشارك في مشروع
    for project_id in project_ids:
        participants = random.sample(researcher_ids, random.randint(2, min(5, len(researcher_ids))))
        for participant_id in participants:
            if neo4j.create_project_participation(participant_id, project_id):
                relationships_created['PARTICIPATED_IN'] += 1

    for publication_id in publication_ids:
        authors = random.sample(researcher_ids, random.randint(2, 4))
        for i, author_id in enumerate(authors, 1):
            if neo4j.create_authorship(author_id, publication_id, i):
                relationships_created['AUTHORED'] += 1

        for j in range(len(authors)):
            for k in range(j + 1, len(authors)):
                researcher1_id = authors[j]
                researcher2_id = authors[k]
                if neo4j.create_coauthorship(researcher1_id, researcher2_id, publication_id):
                    relationships_created['CO_AUTHORED_WITH'] += 1

    for publication_id in publication_ids[:len(project_ids)]:
        project_id = random.choice(project_ids)
        if neo4j.create_produced_relationship(project_id, publication_id):
            relationships_created['PRODUCED'] += 1

    for i in range(len(researcher_ids) * 2):
        researcher1 = random.choice(researcher_ids)
        researcher2 = random.choice(researcher_ids)
        if researcher1 != researcher2:
            if random.random() > 0.5:
                if neo4j.create_teamwork(researcher1, researcher2):
                    relationships_created['TEAMWORK_WITH'] += 1

    return relationships_created


print(f"{Fore.CYAN}{'=' * 70}")
print(f"{Fore.YELLOW}CREATING LARGE SAMPLE DATA FOR TESTING")
print(f"{Fore.YELLOW}TARGET: 100 Researchers, 50 Projects, 30 Publications")
print(f"{Fore.CYAN}{'=' * 70}")

try:
    from app.database.mongodb import mongodb
    from app.database.neo4j import neo4j
    from app.database.redis import redis_manager

    print(f"\n{Fore.GREEN}Database modules imported successfully")

    print(f"\n{Fore.YELLOW}Step 1: Cleaning existing data...")
    if mongodb.client:
        collections = ['researchers', 'projects', 'publications']
        for collection in collections:
            count = mongodb.db[collection].count_documents({})
            if count > 0:
                result = mongodb.db[collection].delete_many({})
                print(f"{Fore.YELLOW}   Deleted {result.deleted_count} documents from {collection}")

    print(f"\n{Fore.YELLOW}Step 2: Creating 100 Researchers...")
    researchers_data = generate_researcher_data(100)
    researcher_ids = []

    for i, researcher_data in enumerate(researchers_data, 1):
        researcher_id = mongodb.create_researcher(researcher_data)
        if researcher_id:
            researcher_ids.append(researcher_id)

            neo4j.create_researcher_node({
                'id': researcher_id,
                'name': researcher_data['name'],
                'email': researcher_data['email'],
                'department': researcher_data['department'],
                'profile_status': researcher_data['profile_status']
            })

            if i % 20 == 0:
                print(f"{Fore.GREEN}   Created {i} researchers...")

    print(f"{Fore.GREEN}SUCCESS: Created {len(researcher_ids)} researchers")

    print(f"\n{Fore.YELLOW}Step 3: Creating 50 Projects...")
    projects_data = generate_project_data(50, researcher_ids)
    project_ids = []

    for i, project_data in enumerate(projects_data, 1):
        project_id = mongodb.create_project(project_data)
        if project_id:
            project_ids.append(project_id)

            if i % 10 == 0:
                print(f"{Fore.GREEN}   Created {i} projects...")

    print(f"{Fore.GREEN}SUCCESS: Created {len(project_ids)} projects")


    # هنا ضع الكود الجديد
    print(f"{Fore.YELLOW}   Creating project nodes in Neo4j...")
    for i, project_data in enumerate(projects_data, 1):
        project_id = project_ids[i - 1] if i - 1 < len(project_ids) else None
        if project_id:
            neo4j.create_project_node({
                'id': project_id,
                'title': project_data['title'],
                'creator_id': project_data['creator_id'],
                'status': project_data['status']
            })
    print(f"\n{Fore.YELLOW}Step 4: Creating 30 Publications...")
    publications_data = generate_publication_data(30, researcher_ids)
    publication_ids = []

    for i, publication_data in enumerate(publications_data, 1):
        publication_id = mongodb.create_publication(publication_data)
        if publication_id:
            publication_ids.append(publication_id)

            if i % 5 == 0:
                print(f"{Fore.GREEN}   Created {i} publications...")

    print(f"{Fore.GREEN}SUCCESS: Created {len(publication_ids)} publications")



    print(f"{Fore.YELLOW}   Creating publication nodes in Neo4j...")
    for j, publication_data in enumerate(publications_data, 1):
        publication_id = publication_ids[j - 1] if j - 1 < len(publication_ids) else None
        if publication_id:
            neo4j.create_publication_node({
                'id': publication_id,
                'title': publication_data['title'],
                'year': publication_data['year']
            })
    print(f"\n{Fore.YELLOW}Step 5: Creating All Relationships...")
    relationships_created = create_diverse_relationships(researcher_ids, project_ids, publication_ids)

    print(f"\n{Fore.GREEN}Relationships Created:")
    for rel_type, count in relationships_created.items():
        if count > 0:
            print(f"   {rel_type}: {count} relationships")

    total_relationships = sum(relationships_created.values())
    print(f"\n{Fore.GREEN}TOTAL RELATIONSHIPS CREATED: {total_relationships}")

    print(f"\n{Fore.YELLOW}Step 6: Redis Caching...")
    if redis_manager.is_connected():
        try:
            redis_manager.client.set("large_dataset:created", get_utc_now().isoformat(), ex=600)
            redis_manager.client.set("large_dataset:researchers", len(researcher_ids), ex=600)
            redis_manager.client.set("large_dataset:projects", len(project_ids), ex=600)
            redis_manager.client.set("large_dataset:publications", len(publication_ids), ex=600)
            redis_manager.client.set("large_dataset:relationships", total_relationships, ex=600)

            print(f"{Fore.GREEN}   Data cached in Redis")
        except Exception as e:
            print(f"{Fore.YELLOW}   Redis caching error: {e}")

    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.GREEN}LARGE DATASET CREATION COMPLETED!")
    print(f"\n{Fore.YELLOW}Summary:")
    print(f"{Fore.WHITE}Researchers: {len(researcher_ids)}")
    print(f"{Fore.WHITE}Projects: {len(project_ids)}")
    print(f"{Fore.WHITE}Publications: {len(publication_ids)}")
    print(f"{Fore.WHITE}Total Relationships: {total_relationships}")

    print(f"\n{Fore.YELLOW}Relationships Breakdown:")
    for rel_type, count in relationships_created.items():
        if count > 0:
            print(f"{Fore.WHITE}  {rel_type}: {count}")

    print(f"\n{Fore.YELLOW}Sample Credentials (all use 'password123'):")
    print(f"{Fore.WHITE}Admin: admin@university.edu")
    print(f"{Fore.WHITE}Random researcher: {researchers_data[0]['email']}")
    print(f"{Fore.WHITE}Random researcher: {researchers_data[50]['email']}")

    print(f"\n{Fore.YELLOW}Next steps:")
    print(f"{Fore.WHITE}1. Check MongoDB: python check_mongodb.py")
    print(f"{Fore.WHITE}2. Check Neo4j: http://localhost:7474")
    print(f"{Fore.WHITE}3. Run system: python run.py")
    print(f"{Fore.WHITE}4. View statistics: python run.py 5")

    print(f"{Fore.CYAN}{'=' * 70}")

except Exception as e:
    print(f"{Fore.RED}Error creating large dataset: {e}")
    import traceback

    traceback.print_exc()