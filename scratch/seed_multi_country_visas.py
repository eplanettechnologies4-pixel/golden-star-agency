import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.visa.models import VisaPackage

multi_country_samples = [
    {
        "country": "Dubai + Baku + Turkey Trio Tour",
        "title": "Middle East & Caucasus 3-Country Combo Visa Special",
        "visa_type": "Trio Tour Combo eVisa",
        "processing_time": "5 to 7 Working Days",
        "stay_validity": "20 Days Total Stay",
        "visa_validity": "90 Days Validity",
        "entry_type": "multiple",
        "price": Decimal("145000.00"),
        "required_documents": "Passport Copy (6 Months Validity), White Background Photos, CNIC Copy, Flight & Hotel Bookings",
        "description": "Exclusive Trio Tour Combo Plan covering Dubai (7 Days), Baku (5 Days), and Istanbul (8 Days) with full visa processing for all 3 destinations.",
        "is_popular": True,
        "is_multi_country": True,
        "countries_included": "UAE (Dubai), Azerbaijan (Baku), Turkey (Istanbul)",
        "tour_destinations": [
            {"country": "UAE (Dubai)", "stay_days": "7 Days", "visa_type": "30-Day Tourist eVisa"},
            {"country": "Azerbaijan (Baku)", "stay_days": "5 Days", "visa_type": "Easy ASAN eVisa"},
            {"country": "Turkey (Istanbul)", "stay_days": "8 Days", "visa_type": "Sticker / Official eVisa"}
        ]
    },
    {
        "country": "Malaysia + Thailand + Singapore Trio Tour",
        "title": "South East Asia Triple Country Explorer Visa Plan",
        "visa_type": "ASEAN Triple Combo Visa",
        "processing_time": "7 to 10 Working Days",
        "stay_validity": "25 Days Total Stay",
        "visa_validity": "60 Days Validity",
        "entry_type": "multiple",
        "price": Decimal("165000.00"),
        "required_documents": "Passport Copy, 2 White Background Photos, Bank Statement (6 Months), CNIC",
        "description": "Complete South East Asia multi-destination package featuring Malaysia eNTRI, Thailand Tourist Visa, and Singapore e-Visa.",
        "is_popular": True,
        "is_multi_country": True,
        "countries_included": "Malaysia (Kuala Lumpur), Thailand (Bangkok), Singapore",
        "tour_destinations": [
            {"country": "Malaysia (Kuala Lumpur)", "stay_days": "8 Days", "visa_type": "eVisa / eNTRI"},
            {"country": "Thailand (Bangkok & Phuket)", "stay_days": "10 Days", "visa_type": "Single Entry Sticker Visa"},
            {"country": "Singapore", "stay_days": "7 Days", "visa_type": "Subclass eVisa"}
        ]
    },
    {
        "country": "Euro Schengen Trio Tour (France, Italy, Switzerland)",
        "title": "Europe Grand Trio Tour Schengen Visa Advisory Plan",
        "visa_type": "Schengen C-Type Visitor Visa",
        "processing_time": "15 to 20 Working Days",
        "stay_validity": "30 Days Stay",
        "visa_validity": "90 Days Validity",
        "entry_type": "multiple",
        "price": Decimal("285000.00"),
        "required_documents": "Passport (6 Months), Bank Statement (6 Months PK 1.5M+), Tax Returns, FRC / MRC, Hotel & Flight Itinerary",
        "description": "Full Schengen Trio Tour assistance including appointment scheduling, travel insurance, and complete file preparation for Paris, Rome, and Zurich.",
        "is_popular": True,
        "is_multi_country": True,
        "countries_included": "France (Paris), Italy (Rome), Switzerland (Zurich)",
        "tour_destinations": [
            {"country": "France (Paris)", "stay_days": "10 Days", "visa_type": "Schengen Short-Stay"},
            {"country": "Italy (Rome & Venice)", "stay_days": "10 Days", "visa_type": "Schengen Transit / Visitor"},
            {"country": "Switzerland (Zurich & Interlaken)", "stay_days": "10 Days", "visa_type": "Schengen Tourist"}
        ]
    }
]

created_count = 0
for data in multi_country_samples:
    vp, created = VisaPackage.objects.get_or_create(
        country=data["country"],
        title=data["title"],
        defaults=data
    )
    if not created:
        for k, v in data.items():
            setattr(vp, k, v)
        vp.save()
    created_count += 1

print(f"SUCCESS: Successfully created {created_count} Multi-Country Trio Tour Visa Packages!")
