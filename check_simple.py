import sys

sys.path.append('.')
from pymongo import MongoClient
import os

client = MongoClient('mongodb://localhost:27017')
db = client['research_collab_db']

count = db.researchers.count_documents({})
print(f"عدد الباحثين في MongoDB: {count}")

print("\nأول 3 باحثين:")
researchers = db.researchers.find().limit(3)
for i, r in enumerate(researchers, 1):
    print(f"{i}. {r.get('name')} - {r.get('email')}")

email_to_delete = input("\nأدخل إيميل باحث تبي تحذفه (أو اضغط Enter للتخطي): ").strip()

if email_to_delete:
    researcher = db.researchers.find_one({'email': email_to_delete})
    if researcher:
        print(f"\nوجدت الباحث: {researcher['name']}")
        confirm = input("تأكيد الحذف؟ اكتب 'نعم': ").strip()

        if confirm == 'نعم':
            result = db.researchers.update_one(
                {'_id': researcher['_id']},
                {'$set': {'profile_status': 'deleted'}}
            )

            if result.modified_count > 0:
                print("✓ تم تحديث حالة الباحث إلى 'محذوف'")
                print("ملاحظة: هذا حذف سطحي (soft delete)، البيانات موجودة لكن الحالة تغيرت")
            else:
                print("✗ فشل في تحديث الحالة")
    else:
        print("✗ ما لقيت باحث بهذا الإيميل")