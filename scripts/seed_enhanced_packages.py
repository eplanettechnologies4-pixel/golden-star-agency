import sys
import os

# Add core_admin folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.packages.models import Package
from apps.bookings.models import Booking
from django.contrib.auth import get_user_model

User = get_user_model()

print("--- Seeding Enhanced Packages ---")

packages_data = [
    {
        "title": "15-Day Economy Star Umrah Package",
        "description": "Budget-conscious family Umrah package including direct flight bookings, visa assistance, and quad rooms with shuttle service to Haram.",
        "price": 245000.00,
        "category": "umrah",
        "duration_days": 15,
        "airline": "PIA",
        "flight_routes": "KHI - JED - MED - KHI",
        "makkah_hotel_name": "Emaar Elite Hotel Makkah",
        "makkah_hotel_distance": "800m with 24/7 Shuttle",
        "madinah_hotel_name": "Emaar Royal Hotel Madinah",
        "madinah_hotel_distance": "350m from Markazia",
        "luggage_weight": "20 kg + 7 kg Hand Carry",
        "images": ["/static/images/umrah_card.png", "/static/images/hajj_card.png"],
        "total_seats": 30,
        "available_seats": 30
    },
    {
        "title": "18-Day Comfort Standard Umrah",
        "description": "Ideal balance of proximity and price. Under 400m from Haram Makkah and 150m from Prophet's Mosque in Madinah.",
        "price": 285000.00,
        "category": "umrah",
        "duration_days": 18,
        "airline": "Saudi Airlines",
        "flight_routes": "ISB - JED - MED - ISB",
        "makkah_hotel_name": "Anjum Hotel Makkah",
        "makkah_hotel_distance": "350m from Haram",
        "madinah_hotel_name": "Pullman Zamzam Madinah",
        "madinah_hotel_distance": "150m from Prophet's Mosque",
        "luggage_weight": "30 kg + 7 kg Hand Carry",
        "images": ["/static/images/hajj_card.png", "/static/images/umrah_banner.png"],
        "total_seats": 30,
        "available_seats": 28
    },
    {
        "title": "28-Day Ramadan & Executive Umrah",
        "description": "Extended 28-day luxury stay for full spiritual devotion with front-row Haram views and high-speed Haramain train transfers.",
        "price": 495000.00,
        "category": "umrah",
        "duration_days": 28,
        "airline": "FlyDubai",
        "flight_routes": "LHR - JED - MED - LHR",
        "makkah_hotel_name": "Swissôtel Al Maqam Makkah",
        "makkah_hotel_distance": "0m (Clock Tower)",
        "madinah_hotel_name": "Dar Al Taqwa Madinah",
        "madinah_hotel_distance": "50m from Courtyard",
        "luggage_weight": "40 kg (2 Pieces) + 7 kg Carry",
        "images": ["/static/images/turkey_card.png", "/static/images/hero_bg.png"],
        "total_seats": 30,
        "available_seats": 25
    },
    {
        "title": "15-Day Shifting Economy Hajj 2026",
        "description": "Official shifting Hajj package with air-conditioned Azizia building lodging during peak days and Maktab B Mina tents.",
        "price": 980000.00,
        "category": "hajj",
        "duration_days": 15,
        "airline": "Saudi Airlines",
        "flight_routes": "KHI - JED - MED - KHI",
        "makkah_hotel_name": "Shifting Azizia Towers",
        "makkah_hotel_distance": "5km (Shifting Days)",
        "madinah_hotel_name": "Markazia 3-Star Hotel",
        "madinah_hotel_distance": "350m from Haram",
        "luggage_weight": "30 kg + 7 kg Hand Carry",
        "images": ["/static/images/hajj_banner.png", "/static/images/hajj_kaaba.png"],
        "total_seats": 30,
        "available_seats": 30
    }
]

created_count = 0
for data in packages_data:
    pkg, created = Package.objects.get_or_create(title=data["title"], defaults=data)
    if not created:
        for k, v in data.items():
            setattr(pkg, k, v)
        pkg.save()
    created_count += 1
    print(f"[{'CREATED' if created else 'UPDATED'}] {pkg.title} ({pkg.duration_days} Days) - Seats: {pkg.available_seats}/{pkg.total_seats}")

print(f"\nSuccessfully seeded {created_count} enhanced packages with dynamic backend options.")
