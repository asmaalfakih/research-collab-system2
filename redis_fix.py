
import redis
import ssl
from dotenv import load_dotenv
import os

load_dotenv()

def test_redis_with_ssl_fix():

    print("Testing Redis SSL Connection Fix...")
    print("=" * 60)

    host = os.getenv("REDIS_HOST")
    port = int(os.getenv("REDIS_PORT"))
    password = os.getenv("REDIS_PASSWORD")
    username = os.getenv("REDIS_USERNAME", "default")

    print(f"Host: {host}:{port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * 8 if password else 'None'}")

    print("\nTesting different connection methods...")
    print("-" * 40)

    test_cases = [
        {
            "name": "Method 1: Without SSL",
            "kwargs": {"ssl": False}
        },
        {
            "name": "Method 2: SSL with CERT_NONE",
            "kwargs": {"ssl": True, "ssl_cert_reqs": ssl.CERT_NONE}
        },
        {
            "name": "Method 3: SSL with username",
            "kwargs": {"ssl": True, "ssl_cert_reqs": ssl.CERT_NONE, "username": username}
        },
        {
            "name": "Method 4: No SSL, with socket_timeout",
            "kwargs": {"ssl": False, "socket_timeout": 10, "socket_connect_timeout": 10}
        },
        {
            "name": "Method 5: Basic connection (no ssl param)",
            "kwargs": {}
        }
    ]

    successful_method = None

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}:")
        print(f"   Settings: {test_case['kwargs']}")

        try:
            connection_kwargs = {
                'host': host,
                'port': port,
                'password': password,
                'decode_responses': True,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
            }

            connection_kwargs.update(test_case['kwargs'])

            r = redis.Redis(**connection_kwargs)

            if r.ping():
                print(f"   SUCCESS!")
                successful_method = test_case

                try:
                    r.set("redis_fix_test", "Hello from Python!")
                    value = r.get("redis_fix_test")
                    print(f"   SET/GET test: {value}")

                    r.hset("test_hash", mapping={"field1": "value1", "field2": "value2"})
                    hash_data = r.hgetall("test_hash")
                    print(f"   HASH test: {hash_data}")

                    info = r.info()
                    print(f"   Redis version: {info.get('redis_version')}")
                    print(f"   Memory: {info.get('used_memory_human')}")

                    r.delete("redis_fix_test")
                    r.delete("test_hash")

                except Exception as e:
                    print(f"   Operations test failed: {e}")

                break

            else:
                print(f"   Ping failed")

        except redis.AuthenticationError as e:
            print(f"   Authentication failed: Check username/password")
        except redis.ConnectionError as e:
            print(f"   Connection error: {str(e)[:80]}")
        except Exception as e:
            print(f"   Error: {type(e).__name__}: {str(e)[:80]}")

    print("\n" + "=" * 60)

    if successful_method:
        print("SUCCESSFUL CONNECTION FOUND!")
        print(f"Method: {successful_method['name']}")
        print(f"Settings: {successful_method['kwargs']}")

        print("\nRecommended .env settings:")
        print("-" * 40)

        env_settings = [
            f"REDIS_HOST={host}",
            f"REDIS_PORT={port}",
            f"REDIS_PASSWORD={password}",
            f"REDIS_USERNAME={username}"
        ]

        if successful_method['kwargs'].get('ssl') == True:
            env_settings.append("REDIS_SSL=True")
            env_settings.append("REDIS_SSL_CERT_REQS=None")
        else:
            env_settings.append("REDIS_SSL=False")

        for setting in env_settings:
            print(setting)

        print("\nCopy these settings to your .env file")

    else:
        print("ALL CONNECTION ATTEMPTS FAILED")
        print("\nTroubleshooting steps:")
        print("1. Check Redis Cloud dashboard")
        print("2. Verify your password is correct")
        print("3. Try using REDIS_SSL=False")
        print("4. Check if port 19404 is blocked by firewall")
        print("5. Try connecting from another network")

    return successful_method

def update_env_file(recommended_settings):
    if not recommended_settings:
        return False

    env_file = ".env"

    if not os.path.exists(env_file):
        print(f"\n{env_file} not found!")
        return False

    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()

        new_lines = []
        redis_updated = False

        for line in lines:
            if line.strip() and not line.startswith('#') and 'REDIS_' in line:
                continue
            new_lines.append(line)

        new_lines.append("\n# Redis Configuration (Auto-updated)\n")
        for setting in recommended_settings:
            new_lines.append(setting + "\n")

        with open(env_file, 'w') as f:
            f.writelines(new_lines)

        print(f"\n{env_file} updated successfully!")
        return True

    except Exception as e:
        print(f"\nFailed to update .env: {e}")
        return False

def main():
    print("Redis Connection Fix Tool")
    print("=" * 60)

    if not os.path.exists(".env"):
        print(".env file not found!")
        print("Please create .env file first")
        return

    successful_method = test_redis_with_ssl_fix()

    if successful_method:
        host = os.getenv("REDIS_HOST")
        port = int(os.getenv("REDIS_PORT"))
        password = os.getenv("REDIS_PASSWORD")
        username = os.getenv("REDIS_USERNAME", "default")

        recommended = [
            f"REDIS_HOST={host}",
            f"REDIS_PORT={port}",
            f"REDIS_PASSWORD={password}",
            f"REDIS_USERNAME={username}"
        ]

        if successful_method['kwargs'].get('ssl') == True:
            recommended.append("REDIS_SSL=True")
            recommended.append("REDIS_SSL_CERT_REQS=None")
        else:
            recommended.append("REDIS_SSL=False")

        update = input("\nUpdate .env file automatically? (yes/no): ").strip().lower()

        if update in ['yes', 'y']:
            update_env_file(recommended)
        else:
            print("\nManual update required. Copy settings above to .env")

    print("\n" + "=" * 60)
    print("Fix tool completed. Run 'python run.py 2' to test connections.")

if __name__ == "__main__":
    main()