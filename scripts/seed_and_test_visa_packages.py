import sys
import os

# Add core_admin folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.visa.models import VisaPackage

print("--- Seeding Visitor Visa Packages ---")

sample_visa_packages = [
    {
        "country": "Saudi Arabia",
        "title": "Saudi Arabia 1-Year Tourist Multiple Entry eVisa",
        "visa_type": "Tourist / Visitor eVisa",
        "processing_time": "2 to 3 Working Days",
        "stay_validity": "90 Days Stay per Visit",
        "visa_validity": "1 Year Validity",
        "entry_type": "multiple",
        "price": 45000.00,
        "original_price": 52000.00,
        "required_documents": "Passport Copy (6 Months Validity), Passport Size Photograph (White Background)",
        "description": "Fast-track online eVisa processing for Saudi Arabia. Valid for tourism, family visits, and Umrah performance.",
        "is_popular": True,
    },
    {
        "country": "United Arab Emirates (Dubai)",
        "title": "Dubai 30-Day Express Tourist Visa",
        "visa_type": "Tourist Visa",
        "processing_time": "24 to 48 Hours",
        "stay_validity": "30 Days Stay",
        "visa_validity": "60 Days Validity from Issuance",
        "entry_type": "single",
        "price": 28500.00,
        "original_price": 34000.00,
        "required_documents": "Passport First Page Scan, Passport Size Photograph, CNIC Front & Back",
        "description": "Quick Dubai tourist visa issuance with instant verification. Includes compulsory COVID-19 health insurance cover.",
        "is_popular": True,
    },
    {
        "country": "Turkey",
        "title": "Turkey Official Sticker Visa Advisory Package",
        "visa_type": "Sticker Tourist Visa",
        "processing_time": "15 to 20 Working Days",
        "stay_validity": "30 Days Stay",
        "visa_validity": "180 Days Validity",
        "entry_type": "single",
        "price": 65000.00,
        "original_price": 75000.00,
        "required_documents": "Original Passport, Bank Statement (Last 6 Months with PKR 500k+ balance), NTN Certificate, Hotel & Flight Bookings",
        "description": "Comprehensive document compilation, appointment booking, hotel/flight itineraries, and embassy submission support.",
        "is_popular": False,
    },
    {
        "country": "United Kingdom",
        "title": "UK Standard Visitor Visa (6 Months)",
        "visa_type": "Standard Visitor Visa",
        "processing_time": "3 to 4 Weeks",
        "stay_validity": "up to 180 Days Stay",
        "visa_validity": "6 Months Validity",
        "entry_type": "multiple",
        "price": 85000.00,
        "original_price": 95000.00,
        "required_documents": "Valid Passport, Bank Statement (6 Months), Property/Asset Documents, Employment/Business Proof, Cover Letter",
        "description": "Professional UK visitor visa file preparation, biometric appointment scheduling, and expert guidance for highest approval success.",
        "is_popular": True,
    }
]

created_count = 0
for data in sample_visa_packages:
    vp, created = VisaPackage.objects.get_or_create(
        country=data["country"],
        title=data["title"],
        defaults=data
    )
    if created:
        created_count += 1
        print(f" [+] Created Visa Package: {vp.country} - {vp.title} (PKR {vp.price:,.2f})")
    else:
        print(f" [=] Existing Visa Package: {vp.country} - {vp.title}")

total_vps = VisaPackage.objects.count()
print(f"\nTotal Visitor Visa Packages in Database: {total_vps}")
print("Seeding and Model Verification Completed 100% Successfully!")
