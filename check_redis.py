
import sys

sys.path.append('.')

import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

print("Checking Redis Data...")
print("=" * 60)

r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT')),
    password=os.getenv('REDIS_PASSWORD'),
    ssl=False,
    decode_responses=True
)

if r.ping():
    print("\033[92mRedis is connected\033[0m")

    keys = r.keys("*")
    print(f"\nTotal keys: {len(keys)}")

    print("\nAll keys:")
    for key in keys:
        key_type = r.type(key)
        print(f"  * {key} ({key_type})")

        if key_type == 'string':
            value = r.get(key)
            if value and len(value) < 100:
                print(f"    Value: {value}")
            elif value:
                print(f"    Value: {value[:50]}...")

    print("\nRedis Info:")
    info = r.info()
    print(f"  * Version: {info.get('redis_version')}")
    print(f"  * Memory used: {info.get('used_memory_human')}")
    print(f"  * Connected clients: {info.get('connected_clients')}")

else:
    print("\033[91mRedis is not connected\033[0m")

print("\n" + "=" * 60)
print("\033[92mRedis Check Complete\033[0m")