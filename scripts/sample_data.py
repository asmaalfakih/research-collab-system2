#!/usr/bin/env python3
"""
Create sample data for testing
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import bcrypt

sys.path.append(str(Path(__file__).parent.parent))

from colorama import init, Fore, Style

init(autoreset=True)


def get_utc_now():
    return datetime.utcnow()


print(f"{Fore.CYAN}{'=' * 70}")
print(f"{Fore.YELLOW}CREATING SAMPLE DATA FOR TESTING")
print(f"{Fore.CYAN}{'=' * 70}")

try:
    from app.database.mongodb import mongodb
    from app.database.neo4j import neo4j
    from app.database.redis import redis_manager

    print(f"\n{Fore.GREEN}Database modules imported successfully")

    print(f"\n{Fore.YELLOW}Step 1: Deleting existing test data...")

    if mongodb.client:
        delete_result = mongodb.db.researchers.delete_many({
            'email': {'$in': [
                'ahmed.ali@university.edu',
                'sara.mohamed@university.edu',
                'omar.hassan@university.edu'
            ]}
        })
        print(f"{Fore.GREEN}Deleted {delete_result.deleted_count} existing test researchers")

    print(f"\n{Fore.YELLOW}Step 2: Creating Sample Researchers...")

    sample_researchers = [
        {
            'name': 'Dr. Ahmed Ali',
            'email': 'ahmed.ali@university.edu',
            'password': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'department': 'Computer Science',
            'profile_status': 'approved',
            'role': 'researcher',
            'research_interests': ['AI', 'Machine Learning', 'Data Science'],
            'contact': {'phone': '0599123456', 'city': 'Hebron'},
            'created_at': get_utc_now()
        },
        {
            'name': 'Dr. Sara Mohamed',
            'email': 'sara.mohamed@university.edu',
            'password': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'department': 'Information Technology',
            'profile_status': 'approved',
            'role': 'researcher',
            'research_interests': ['Networks', 'Security', 'Cloud Computing'],
            'contact': {'phone': '0599765432', 'city': 'Ramallah'},
            'created_at': get_utc_now()
        },
        {
            'name': 'Dr. Omar Hassan',
            'email': 'omar.hassan@university.edu',
            'password': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'department': 'Data Science',
            'profile_status': 'approved',
            'role': 'researcher',
            'research_interests': ['Big Data', 'Statistics', 'Data Mining'],
            'contact': {'phone': '0599888777', 'city': 'Bethlehem'},
            'created_at': get_utc_now()
        }
    ]

    researcher_ids = []
    for researcher_data in sample_researchers:
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
            print(f"{Fore.GREEN}{researcher_data['name']} - {researcher_id}")
        else:
            print(f"{Fore.RED}Failed to create {researcher_data['name']}")

    print(f"{Fore.WHITE}Total researchers created: {len(researcher_ids)}")

    print(f"\n{Fore.YELLOW}Step 3: Creating Diverse Relationships...")

    if len(researcher_ids) >= 3:
        # Ahmed & Sara: Multiple relationship types
        count1 = neo4j.create_coauthorship(researcher_ids[0], researcher_ids[1])
        count2 = neo4j.create_teamwork(researcher_ids[0], researcher_ids[1])

        # Ahmed & Omar: Different relationship types
        count3 = neo4j.create_coauthorship(researcher_ids[0], researcher_ids[2])
        count4 = neo4j.create_supervision(researcher_ids[0], researcher_ids[2])

        # Sara & Omar: Teamwork
        count5 = neo4j.create_teamwork(researcher_ids[1], researcher_ids[2])

        r1 = mongodb.get_researcher(researcher_ids[0])
        r2 = mongodb.get_researcher(researcher_ids[1])
        r3 = mongodb.get_researcher(researcher_ids[2])

        if r1 and r2:
            print(f"{Fore.GREEN}Ahmed Ali & Sara Mohamed: CO_AUTHORED_WITH & TEAMWORK_WITH")
        if r1 and r3:
            print(f"{Fore.GREEN}Ahmed Ali & Omar Hassan: CO_AUTHORED_WITH & SUPERVISED")
        if r2 and r3:
            print(f"{Fore.GREEN}Sara Mohamed & Omar Hassan: TEAMWORK_WITH")

    print(f"\n{Fore.YELLOW}Step 4: Creating Sample Project...")

    if len(researcher_ids) >= 2:
        project_data = {
            'title': 'AI in Healthcare Research',
            'description': 'Research on applying machine learning to healthcare diagnostics',
            'creator_id': researcher_ids[0],
            'creator_name': 'Dr. Ahmed Ali',
            'participants': researcher_ids[:2],
            'start_date': get_utc_now().date().isoformat(),
            'end_date': (get_utc_now() + timedelta(days=180)).date().isoformat(),
            'status': 'active',
            'research_area': 'Artificial Intelligence',
            'tags': ['AI', 'Healthcare', 'Machine Learning'],
            'budget': 50000.0,
            'funding_source': 'University Research Grant',
            'created_at': get_utc_now(),
            'updated_at': get_utc_now()
        }

        project_id = mongodb.create_project(project_data)
        if project_id:
            print(f"{Fore.GREEN}Project created: {project_data['title']}")
            print(f"{Fore.WHITE}ID: {project_id}")

            # Create project participation relationships
            for participant_id in project_data['participants']:
                neo4j.create_project_participation(participant_id, project_id)
            print(f"{Fore.GREEN}Project participation relationships created")
        else:
            print(f"{Fore.RED}Failed to create project")

    print(f"\n{Fore.YELLOW}Step 5: Creating Sample Publication...")

    if len(researcher_ids) >= 2:
        publication_data = {
            'title': 'Deep Learning Approaches for Medical Image Analysis',
            'authors': [
                {
                    'researcher_id': researcher_ids[0],
                    'name': 'Dr. Ahmed Ali',
                    'order': 1,
                    'affiliation': 'Computer Science Department',
                    'contribution': 'Lead researcher'
                },
                {
                    'researcher_id': researcher_ids[1],
                    'name': 'Dr. Sara Mohamed',
                    'order': 2,
                    'affiliation': 'IT Department',
                    'contribution': 'Data analysis'
                }
            ],
            'year': 2024,
            'doi': '10.1000/sample124',  # Changed DOI to avoid duplicate
            'journal': 'Journal of Medical AI',
            'abstract': 'This paper presents novel deep learning approaches...',
            'keywords': ['Deep Learning', 'Medical Imaging', 'AI'],
            'citation_count': 15,
            'status': 'published',
            'views': 300,
            'downloads': 150,
            'created_at': get_utc_now(),
            'updated_at': get_utc_now()
        }

        publication_id = mongodb.create_publication(publication_data)
        if publication_id:
            print(f"{Fore.GREEN}Publication created: {publication_data['title']}")
            print(f"{Fore.WHITE}ID: {publication_id}")
        else:
            print(f"{Fore.RED}Failed to create publication")

    print(f"\n{Fore.YELLOW}Step 6: Redis Caching...")

    if redis_manager.is_connected():
        try:
            redis_manager.client.set("sample_data:created", get_utc_now().isoformat(), ex=300)
            redis_manager.client.set("sample_data:researcher_count", len(researcher_ids), ex=300)
            print(f"{Fore.GREEN}Simple caching completed")

            keys = redis_manager.client.keys("*")
            print(f"{Fore.WHITE}Total keys in Redis: {len(keys)}")
        except Exception as e:
            print(f"{Fore.YELLOW}Redis caching error: {e}")

    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.GREEN}SAMPLE DATA CREATION COMPLETED!")
    print(f"\n{Fore.YELLOW}Summary:")
    print(f"{Fore.WHITE}Researchers: {len(researcher_ids)}")
    print(f"{Fore.WHITE}Projects: {1 if 'project_id' in locals() else 0}")
    print(f"{Fore.WHITE}Publications: {1 if 'publication_id' in locals() else 0}")

    print(f"\n{Fore.YELLOW}Test Credentials:")
    print(f"{Fore.WHITE}Admin: admin@university.edu / admin123")
    print(f"{Fore.WHITE}Researcher 1: ahmed.ali@university.edu / password123")
    print(f"{Fore.WHITE}Researcher 2: sara.mohamed@university.edu / password123")
    print(f"{Fore.WHITE}Researcher 3: omar.hassan@university.edu / password123")

    print(f"\n{Fore.YELLOW}Next steps:")
    print(f"{Fore.WHITE}1. Check MongoDB: python check_mongodb.py")
    print(f"{Fore.WHITE}2. Check Neo4j in browser: http://localhost:7474")
    print(f"{Fore.WHITE}3. Run main system: python run.py")

    print(f"{Fore.CYAN}{'=' * 70}")

except Exception as e:
    print(f"{Fore.RED}Error creating sample data: {e}")
    import traceback

    traceback.print_exc()