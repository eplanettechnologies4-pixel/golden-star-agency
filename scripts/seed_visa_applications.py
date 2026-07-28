import sys
import os

# Add core_admin folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.visa.models import VisaApplication
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(role='admin').first() or User.objects.first()

print("--- Seeding Visitor & Tourist Visa Applications ---")

sample_visas = [
    {
        "full_name": "Muhammad Hamza Khan",
        "email": "hamza.khan@gmail.com",
        "phone": "+92 300 1234567",
        "country": "Saudi Arabia",
        "visa_type": "Umrah Tourist eVisa (1-Year Multiple Entry)",
        "passport_number": "PK-8849201",
        "status": "pending"
    },
    {
        "full_name": "Ayesha Tariq Siddiqui",
        "email": "ayesha.siddiqui@yahoo.com",
        "phone": "+92 321 9876543",
        "country": "United Arab Emirates",
        "visa_type": "Dubai 30-Day Tourist Visa",
        "passport_number": "PK-9923412",
        "status": "submitted"
    },
    {
        "full_name": "Tariq Mahmood",
        "email": "tariq.mahmood@hotmail.com",
        "phone": "+92 333 4567890",
        "country": "Turkey",
        "visa_type": "Turkey Tourist eVisa (Single Entry)",
        "passport_number": "PK-7741098",
        "status": "approved"
    }
]

for item in sample_visas:
    visa, created = VisaApplication.objects.get_or_create(
        user=admin_user,
        passport_number=item["passport_number"],
        defaults=item
    )
    if not created:
        for k, v in item.items():
            setattr(visa, k, v)
        visa.save()
    print(f"[{'CREATED' if created else 'UPDATED'}] Applicant: {visa.get_applicant_name()} | {visa.visa_type} | Status: {visa.status}")

print("Visa Applications Seeding Completed!\n")
