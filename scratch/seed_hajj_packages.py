import os
import sys
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.airline_ticketing.models import AgentHajjPackage, AgentHajjAccommodation

dummy_packages = [
    {
        "title": "Executive VIP Shifting Hajj Package (40 Days)",
        "description": "5-Star Luxury Hajj package with VIP Air-Conditioned Mina tents, gourmet buffet meals, and clock tower accommodations in Makkah & Madinah.",
        "duration_days": 40,
        "price_sharing": Decimal("2450000.00"),
        "price_quad": Decimal("2650000.00"),
        "price_triple": Decimal("2850000.00"),
        "price_double": Decimal("3150000.00"),
        "hajj_operator_name": "Al-Harmain Executive Hajj Group",
        "license_number": "HGO-1001",
        "saudi_registration_number": "KSA-VIP-881",
        "departure_date": date(2026, 5, 20),
        "return_date": date(2026, 6, 29),
        "includes_meal": True,
        "meal_detail": "Full Board International Buffet + Mina Snack Box",
        "airline_name": "Saudi Airlines",
        "flight_name": "SV-705 / SV-706",
        "flight_route": "KHI - JED - MED - KHI",
        "makkah_hotel_name": "Swissôtel Al Maqam Makkah",
        "makkah_hotel_distance": "0m (Clock Tower)",
        "madinah_hotel_name": "Dar Al Taqwa Madinah",
        "madinah_hotel_distance": "50m from Haram",
        "total_seats": 50,
        "available_seats": 38,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Swissôtel Al Maqam Makkah", "manual_hotel_distance": "0m (Clock Tower)", "nights": 15},
            {"city": "makkah", "manual_hotel_name": "VIP Azizia Air-Conditioned Building", "manual_hotel_distance": "Shifting (Mina Access)", "nights": 15},
            {"city": "madinah", "manual_hotel_name": "Dar Al Taqwa Madinah", "manual_hotel_distance": "50m from Haram", "nights": 10}
        ]
    },
    {
        "title": "Luxury Non-Shifting Direct Hajj Package (25 Days)",
        "description": "Exclusive Non-Shifting Hajj package staying throughout in Makkah Haram clock tower with direct flights and dedicated guide service.",
        "duration_days": 25,
        "price_sharing": Decimal("2950000.00"),
        "price_quad": Decimal("3150000.00"),
        "price_triple": Decimal("3450000.00"),
        "price_double": Decimal("3850000.00"),
        "hajj_operator_name": "Golden Star VIP Hajj Services",
        "license_number": "HGO-1002",
        "saudi_registration_number": "KSA-VIP-882",
        "departure_date": date(2026, 5, 25),
        "return_date": date(2026, 6, 18),
        "includes_meal": True,
        "meal_detail": "Full Board Open Buffet + VIP Arafat Tent Services",
        "airline_name": "Saudi Airlines",
        "flight_name": "SV-734 / SV-735",
        "flight_route": "LHE - JED - MED - LHE",
        "makkah_hotel_name": "Fairmont Makkah Clock Royal Tower",
        "makkah_hotel_distance": "0m (Haram Front)",
        "madinah_hotel_name": "Pullman Zamzam Madinah",
        "madinah_hotel_distance": "100m from Haram",
        "total_seats": 40,
        "available_seats": 22,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Fairmont Makkah Clock Royal Tower", "manual_hotel_distance": "0m (Haram Front)", "nights": 15},
            {"city": "madinah", "manual_hotel_name": "Pullman Zamzam Madinah", "manual_hotel_distance": "100m from Haram", "nights": 10}
        ]
    },
    {
        "title": "Economy Shifting Hajj Package (40 Days)",
        "description": "Budget-friendly 40-day Hajj package with Category A Azizia building accommodation, 24/7 bus transfer, and full religious guidance.",
        "duration_days": 40,
        "price_sharing": Decimal("1350000.00"),
        "price_quad": Decimal("1450000.00"),
        "price_triple": Decimal("1600000.00"),
        "price_double": Decimal("1800000.00"),
        "hajj_operator_name": "Labbaik Pilgrim Services",
        "license_number": "HGO-1003",
        "saudi_registration_number": "KSA-ECO-701",
        "departure_date": date(2026, 5, 18),
        "return_date": date(2026, 6, 27),
        "includes_meal": True,
        "meal_detail": "Three Meals Daily (Pakistani Menu)",
        "airline_name": "PIA (Pakistan International Airlines)",
        "flight_name": "PK-741 / PK-742",
        "flight_route": "ISB - JED - MED - ISB",
        "makkah_hotel_name": "Azizia Building Category A",
        "makkah_hotel_distance": "24/7 Shuttle to Haram",
        "madinah_hotel_name": "Markaziah Hotel Madinah",
        "madinah_hotel_distance": "400m from Haram",
        "total_seats": 60,
        "available_seats": 45,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Azizia Building Category A", "manual_hotel_distance": "24/7 Shuttle to Haram", "nights": 25},
            {"city": "madinah", "manual_hotel_name": "Markaziah Hotel Madinah", "manual_hotel_distance": "400m from Haram", "nights": 15}
        ]
    },
    {
        "title": "Short Stay Executive Hajj Package (15 Days)",
        "description": "Fast-track 15-day premium Hajj package designed for corporate executives with 5-star hotel luxury and express Mina transfers.",
        "duration_days": 15,
        "price_sharing": Decimal("3200000.00"),
        "price_quad": Decimal("3500000.00"),
        "price_triple": Decimal("3850000.00"),
        "price_double": Decimal("4300000.00"),
        "hajj_operator_name": "Caravan-e-Aqsa Hajj Group",
        "license_number": "HGO-1004",
        "saudi_registration_number": "KSA-EX-550",
        "departure_date": date(2026, 5, 30),
        "return_date": date(2026, 6, 14),
        "includes_meal": True,
        "meal_detail": "5-Star Hotel Buffet + Air-Conditioned Mina Camp Catering",
        "airline_name": "Flynas",
        "flight_name": "XY-881 / XY-882",
        "flight_route": "KHI - JED - JED - KHI",
        "makkah_hotel_name": "Makkah Hotel & Towers",
        "makkah_hotel_distance": "0m (In Haram Plaza)",
        "madinah_hotel_name": "Oberoi Madinah Hotel",
        "madinah_hotel_distance": "0m (Prophet Mosque Courtyard)",
        "total_seats": 30,
        "available_seats": 14,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Makkah Hotel & Towers", "manual_hotel_distance": "0m (In Haram Plaza)", "nights": 8},
            {"city": "madinah", "manual_hotel_name": "Oberoi Madinah Hotel", "manual_hotel_distance": "0m (Prophet Mosque Courtyard)", "nights": 7}
        ]
    },
    {
        "title": "Premium Family Hajj Package (30 Days)",
        "description": "30-day family-friendly Hajj package featuring spacious rooms, close proximity to Haram, and comprehensive Ziyarat in Makkah & Madinah.",
        "duration_days": 30,
        "price_sharing": Decimal("2100000.00"),
        "price_quad": Decimal("2300000.00"),
        "price_triple": Decimal("2550000.00"),
        "price_double": Decimal("2850000.00"),
        "hajj_operator_name": "Al-Falah Hajj & Umrah Pvt Ltd",
        "license_number": "HGO-1005",
        "saudi_registration_number": "KSA-PRM-991",
        "departure_date": date(2026, 5, 22),
        "return_date": date(2026, 6, 21),
        "includes_meal": True,
        "meal_detail": "Full Board Buffet Meal Plan",
        "airline_name": "Saudi Airlines",
        "flight_name": "SV-709 / SV-710",
        "flight_route": "KHI - JED - MED - KHI",
        "makkah_hotel_name": "Anjum Hotel Makkah",
        "makkah_hotel_distance": "350m / Haram Footbridge",
        "madinah_hotel_name": "Anwar Al Madinah Movenpick",
        "madinah_hotel_distance": "50m from Haram",
        "total_seats": 45,
        "available_seats": 30,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Anjum Hotel Makkah", "manual_hotel_distance": "350m / Haram Footbridge", "nights": 18},
            {"city": "madinah", "manual_hotel_name": "Anwar Al Madinah Movenpick", "manual_hotel_distance": "50m from Haram", "nights": 12}
        ]
    },
    {
        "title": "Standard 4-Star Hajj Journey (35 Days)",
        "description": "Comprehensive 35-day Hajj package featuring modern 4-star hotels with 24/7 Haram shuttle service and complete guidance by experienced Islamic scholars.",
        "duration_days": 35,
        "price_sharing": Decimal("1650000.00"),
        "price_quad": Decimal("1800000.00"),
        "price_triple": Decimal("2000000.00"),
        "price_double": Decimal("2250000.00"),
        "hajj_operator_name": "Qafila Al-Madinah Hajj Tour",
        "license_number": "HGO-1006",
        "saudi_registration_number": "KSA-STD-602",
        "departure_date": date(2026, 5, 19),
        "return_date": date(2026, 6, 23),
        "includes_meal": True,
        "meal_detail": "Full Board Pakistani Buffet",
        "airline_name": "PIA (Pakistan International Airlines)",
        "flight_name": "PK-759 / PK-760",
        "flight_route": "LHE - JED - MED - LHE",
        "makkah_hotel_name": "Al Kiswah Towers Makkah",
        "makkah_hotel_distance": "800m (24/7 Express Shuttle)",
        "madinah_hotel_name": "Saja Al Madinah",
        "madinah_hotel_distance": "350m from Haram",
        "total_seats": 50,
        "available_seats": 35,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Al Kiswah Towers Makkah", "manual_hotel_distance": "800m (24/7 Express Shuttle)", "nights": 20},
            {"city": "madinah", "manual_hotel_name": "Saja Al Madinah", "manual_hotel_distance": "350m from Haram", "nights": 15}
        ]
    },
    {
        "title": "VIP Royal Clock Tower Hajj Special (20 Days)",
        "description": "Ultra-luxury Hajj experience staying in Kaaba-view suites at Raffles Makkah Palace with private transport and dedicated personal butler service.",
        "duration_days": 20,
        "price_sharing": Decimal("3800000.00"),
        "price_quad": Decimal("4100000.00"),
        "price_triple": Decimal("4500000.00"),
        "price_double": Decimal("5100000.00"),
        "hajj_operator_name": "Crown Travel Royal Hajj Division",
        "license_number": "HGO-1007",
        "saudi_registration_number": "KSA-ROY-110",
        "departure_date": date(2026, 5, 27),
        "return_date": date(2026, 6, 16),
        "includes_meal": True,
        "meal_detail": "Royal International Buffet & Private Mina Dining",
        "airline_name": "Saudi Airlines",
        "flight_name": "SV-727 / SV-728",
        "flight_route": "ISB - JED - MED - ISB",
        "makkah_hotel_name": "Raffles Makkah Palace",
        "makkah_hotel_distance": "0m (Kaaba View Suite)",
        "madinah_hotel_name": "Madinah Hilton Hotel",
        "madinah_hotel_distance": "50m from Haram",
        "total_seats": 25,
        "available_seats": 10,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Raffles Makkah Palace", "manual_hotel_distance": "0m (Kaaba View Suite)", "nights": 12},
            {"city": "madinah", "manual_hotel_name": "Madinah Hilton Hotel", "manual_hotel_distance": "50m from Haram", "nights": 8}
        ]
    },
    {
        "title": "Express 12-Day Business Class Hajj Package",
        "description": "Ultra-short 12-day Business Class Hajj package with direct flights, 5-star Ibrahim Al Khalil Makkah hotel, and VIP Maktab 1 Mina tents.",
        "duration_days": 12,
        "price_sharing": Decimal("3950000.00"),
        "price_quad": Decimal("4300000.00"),
        "price_triple": Decimal("4750000.00"),
        "price_double": Decimal("5400000.00"),
        "hajj_operator_name": "Premier Hajj Consortium",
        "license_number": "HGO-1008",
        "saudi_registration_number": "KSA-BUS-331",
        "departure_date": date(2026, 6, 1),
        "return_date": date(2026, 6, 13),
        "includes_meal": True,
        "meal_detail": "VIP Business Class Catering",
        "airline_name": "Saudi Airlines",
        "flight_name": "SV-701 / SV-702",
        "flight_route": "KHI - JED - MED - KHI",
        "makkah_hotel_name": "Conrad Makkah Hotel",
        "makkah_hotel_distance": "0m (Ibrahim Al Khalil)",
        "madinah_hotel_name": "Dar Al Iman InterContinental",
        "madinah_hotel_distance": "0m (Haram Plaza)",
        "total_seats": 20,
        "available_seats": 8,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Conrad Makkah Hotel", "manual_hotel_distance": "0m (Ibrahim Al Khalil)", "nights": 7},
            {"city": "madinah", "manual_hotel_name": "Dar Al Iman InterContinental", "manual_hotel_distance": "0m (Haram Plaza)", "nights": 5}
        ]
    },
    {
        "title": "Comfort Shifting Hajj Package (42 Days)",
        "description": "Full 42-day complete spiritual journey with comfortable hotel stays in Makkah & Madinah and dedicated bus shuttles throughout Hajj days.",
        "duration_days": 42,
        "price_sharing": Decimal("1500000.00"),
        "price_quad": Decimal("1650000.00"),
        "price_triple": Decimal("1850000.00"),
        "price_double": Decimal("2100000.00"),
        "hajj_operator_name": "Al-Noor Travel & Tours",
        "license_number": "HGO-1009",
        "saudi_registration_number": "KSA-CMF-441",
        "departure_date": date(2026, 5, 17),
        "return_date": date(2026, 6, 28),
        "includes_meal": True,
        "meal_detail": "Full Board Traditional Menu",
        "airline_name": "Air Arabia",
        "flight_name": "G9-543 / G9-544",
        "flight_route": "KHI - SHJ - JED - KHI",
        "makkah_hotel_name": "Park Inn by Radisson Makkah Al Naseem",
        "makkah_hotel_distance": "Shuttle Service to Haram",
        "madinah_hotel_name": "Grand Plaza Al Madinah",
        "madinah_hotel_distance": "200m from Haram",
        "total_seats": 55,
        "available_seats": 40,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Park Inn by Radisson Makkah Al Naseem", "manual_hotel_distance": "Shuttle Service to Haram", "nights": 22},
            {"city": "madinah", "manual_hotel_name": "Grand Plaza Al Madinah", "manual_hotel_distance": "200m from Haram", "nights": 20}
        ]
    },
    {
        "title": "Five Star Deluxe Haram Front Hajj Special (28 Days)",
        "description": "28-day 5-Star Deluxe Hajj package featuring Address Jabal Omar in Makkah and Shahd Al Madinah in Madinah with full VIP amenities.",
        "duration_days": 28,
        "price_sharing": Decimal("2750000.00"),
        "price_quad": Decimal("2950000.00"),
        "price_triple": Decimal("3250000.00"),
        "price_double": Decimal("3650000.00"),
        "hajj_operator_name": "Universal Hajj & Travel Network",
        "license_number": "HGO-1010",
        "saudi_registration_number": "KSA-DLX-990",
        "departure_date": date(2026, 5, 23),
        "return_date": date(2026, 6, 20),
        "includes_meal": True,
        "meal_detail": "Full Board International Buffet",
        "airline_name": "Saudi Airlines",
        "flight_name": "SV-791 / SV-792",
        "flight_route": "PEW - JED - MED - PEW",
        "makkah_hotel_name": "Address Jabal Omar Makkah",
        "makkah_hotel_distance": "0m (Haram Front)",
        "madinah_hotel_name": "Shahd Al Madinah Hotel",
        "madinah_hotel_distance": "50m from Haram",
        "total_seats": 40,
        "available_seats": 28,
        "is_active": True,
        "accommodations": [
            {"city": "makkah", "manual_hotel_name": "Address Jabal Omar Makkah", "manual_hotel_distance": "0m (Haram Front)", "nights": 16},
            {"city": "madinah", "manual_hotel_name": "Shahd Al Madinah Hotel", "manual_hotel_distance": "50m from Haram", "nights": 12}
        ]
    }
]

created_count = 0
for pkg_data in dummy_packages:
    accommodations = pkg_data.pop("accommodations")
    pkg = AgentHajjPackage.objects.create(**pkg_data)
    for order, acc in enumerate(accommodations):
        AgentHajjAccommodation.objects.create(
            agent_hajj_package=pkg,
            city=acc["city"],
            manual_hotel_name=acc["manual_hotel_name"],
            manual_hotel_distance=acc["manual_hotel_distance"],
            nights=acc["nights"],
            order=order
        )
    created_count += 1

print(f"SUCCESS: Successfully created {created_count} dummy Agent Hajj Packages!")
