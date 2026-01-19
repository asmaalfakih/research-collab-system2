#!/usr/bin/env python3
"""Test Multiple User Sessions"""

import subprocess
import threading
import time
from colorama import init, Fore

init(autoreset=True)

# بيانات الباحثين للتجربة
RESEARCHERS = [
    {"email": "aaron.smith@university.edu", "password": "password123"},
    {"email": "alice.berry@university.edu", "password": "password123"},
    {"email": "alison.lewis@university.edu", "password": "password123"},
    {"email": "andrew.gardner@university.edu", "password": "password123"},
    {"email": "andrew.harrison@university.edu", "password": "password123"}
]


def login_researcher(email, password, session_num):
    """محاكاة تسجيل دخول باحث"""
    print(f"{Fore.CYAN}[Session {session_num}] Logging in: {email}")

    # هنا يمكنك استخدام API حقيقي أو محاكاة
    # هذا مثال مبسط
    time.sleep(1)  # محاكاة وقت الاتصال

    print(f"{Fore.GREEN}[Session {session_num}] {email}: Logged in successfully")

    # محاكاة بعض النشاط
    activities = ["view_profile", "search_researchers", "view_projects"]
    for activity in activities:
        time.sleep(0.5)
        print(f"{Fore.YELLOW}[Session {session_num}] {email}: Performing {activity}")

    return f"session_{session_num}_{email}"


def test_redis_sessions():
    """اختبار الجلسات في Redis"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.YELLOW}TESTING MULTIPLE SESSIONS IN REDIS")
    print(f"{Fore.CYAN}{'=' * 60}")

    # تشغيل 5 جلسات متزامنة
    threads = []
    sessions = []

    for i, researcher in enumerate(RESEARCHERS, 1):
        thread = threading.Thread(
            target=lambda e=researcher['email'], p=researcher['password'], n=i:
            sessions.append(login_researcher(e, p, n))
        )
        threads.append(thread)
        thread.start()

    # انتظار انتهاء جميع الثريدات
    for thread in threads:
        thread.join()

    print(f"\n{Fore.GREEN}All sessions completed!")
    print(f"Total sessions created: {len(sessions)}")

    # عرض الجلسات في Redis
    show_redis_sessions()


def show_redis_sessions():
    """عرض الجلسات النشطة في Redis"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.YELLOW}ACTIVE SESSIONS IN REDIS")
    print(f"{Fore.CYAN}{'=' * 60}")

    try:
        import redis
        from dotenv import load_dotenv
        import os

        load_dotenv()

        r = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            password=os.getenv('REDIS_PASSWORD'),
            ssl=False,
            decode_responses=True
        )

        if r.ping():
            # البحث عن جميع مفاتيح الجلسات
            session_keys = r.keys("session:*")

            print(f"{Fore.GREEN}Total session keys in Redis: {len(session_keys)}")

            if session_keys:
                print(f"\n{Fore.YELLOW}Session Details:")
                for key in session_keys[:10]:  # عرض أول 10 جلسات فقط
                    try:
                        session_data = r.hgetall(key)
                        if session_data:
                            print(f"{Fore.CYAN}Key: {key}")
                            print(f"{Fore.WHITE}  User: {session_data.get('name', 'Unknown')}")
                            print(f"  Email: {session_data.get('email', 'Unknown')}")
                            print(f"  Role: {session_data.get('role', 'Unknown')}")
                            print(f"  Created: {session_data.get('created_at', 'Unknown')}")
                            ttl = r.ttl(key)
                            print(f"  TTL: {ttl} seconds")
                            print()
                    except:
                        pass
            else:
                print(f"{Fore.YELLOW}No active sessions found in Redis")

            # إحصائيات Redis
            info = r.info()
            print(f"\n{Fore.GREEN}Redis Statistics:")
            print(f"{Fore.WHITE}  Connected Clients: {info.get('connected_clients', 0)}")
            print(f"  Total Keys: {r.dbsize()}")
            print(f"  Memory Used: {info.get('used_memory_human', 'N/A')}")

        else:
            print(f"{Fore.RED}Redis connection failed")

    except Exception as e:
        print(f"{Fore.RED}Error checking Redis: {e}")


def check_current_users():
    """فحص المستخدمين النشطين حالياً"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.YELLOW}CURRENT ACTIVE USERS")
    print(f"{Fore.CYAN}{'=' * 60}")

    try:
        from app.database.redis import redis_manager

        if redis_manager and redis_manager.is_connected():
            # البحث عن جميع الجلسات
            session_pattern = "session:*"
            session_keys = redis_manager.client.keys(session_pattern)

            print(f"{Fore.GREEN}Found {len(session_keys)} active session(s)")

            users = {}
            for key in session_keys:
                try:
                    session_data = redis_manager.client.hgetall(key)
                    if session_data:
                        email = session_data.get('email', 'unknown')
                        name = session_data.get('name', 'Unknown')
                        role = session_data.get('role', 'user')

                        if email not in users:
                            users[email] = {
                                'name': name,
                                'role': role,
                                'sessions': 1
                            }
                        else:
                            users[email]['sessions'] += 1
                except:
                    continue

            if users:
                print(f"\n{Fore.YELLOW}Active Users ({len(users)}):")
                for i, (email, data) in enumerate(users.items(), 1):
                    print(f"{Fore.GREEN}[{i}] {data['name']} ({email})")
                    print(f"{Fore.WHITE}   Role: {data['role']}")
                    print(f"   Active Sessions: {data['sessions']}")
                    print()
            else:
                print(f"{Fore.YELLOW}No active users found")

        else:
            print(f"{Fore.YELLOW}Redis manager not connected")

    except Exception as e:
        print(f"{Fore.RED}Error: {e}")


if __name__ == "__main__":
    # اختيار الاختبار المطلوب
    print(f"{Fore.CYAN}Choose test:")
    print(f"{Fore.GREEN}[1] Test multiple sessions")
    print(f"{Fore.GREEN}[2] Check current active users")
    print(f"{Fore.GREEN}[3] Show Redis sessions")

    choice = input(f"{Fore.YELLOW}Select option: ").strip()

    if choice == '1':
        test_redis_sessions()
    elif choice == '2':
        check_current_users()
    elif choice == '3':
        show_redis_sessions()
    else:
        print(f"{Fore.RED}Invalid choice")