import sys
import os
import datetime

# Add core_admin folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.bookings.models import Booking
from apps.visa.models import VisaApplication
from apps.flights.models import FlightQuoteRequest
from apps.packages.models import Package

User = get_user_model()
agent = User.objects.filter(username='Danish').first()

if not agent:
    print("Agent Danish not found. Creating Danish.")
    agent = User.objects.create_user(
        username='Danish',
        email='danish@example.com',
        password='password123',
        role='agent',
        approval_status='approved',
        company_name='Danish Travel Co.',
        first_name='Danish',
        last_name='Ali',
        phone='+92 300 1234567'
    )
else:
    print("Found agent Danish.")

# Clear existing agent data to avoid massive clutter
Booking.objects.filter(user=agent).delete()
VisaApplication.objects.filter(user=agent).delete()
FlightQuoteRequest.objects.filter(user=agent).delete()
print("Cleared old bookings, visas, and flight quotes for Danish.")

# Ensure packages exist
packages = [
    Package.objects.get_or_create(title="Luxury 15-Day Hajj Package", defaults={'description': "Luxury Hajj package with premium lodging", 'price': 950000.00, 'category': "hajj", 'duration_days': 15})[0],
    Package.objects.get_or_create(title="Premium 10-Day Umrah Tour", defaults={'description': "Premium Umrah travel and accommodation", 'price': 350000.00, 'category': "umrah", 'duration_days': 10})[0],
    Package.objects.get_or_create(title="7-Day Istanbul Explorer Tour", defaults={'description': "Explore the beauty of Turkey", 'price': 220000.00, 'category': "tour", 'duration_days': 7})[0],
]

# Seed Bookings
bookings_data = [
    {"package": packages[0], "booking_type": "package", "status": "confirmed", "total_price": 950000.00},
    {"package": packages[1], "booking_type": "package", "status": "confirmed", "total_price": 350000.00},
    {"package": packages[2], "booking_type": "package", "status": "pending", "total_price": 220000.00},
    {"package": None, "booking_type": "custom", "status": "confirmed", "total_price": 180000.00},
    {"package": packages[1], "booking_type": "package", "status": "cancelled", "total_price": 350000.00},
    {"package": packages[0], "booking_type": "package", "status": "pending", "total_price": 950000.00},
    {"package": None, "booking_type": "custom", "status": "confirmed", "total_price": 140000.00},
]
for data in bookings_data:
    Booking.objects.create(user=agent, **data)
print(f"Seeded {len(bookings_data)} bookings.")

# Seed Visa Applications
visas_data = [
    {"country": "Saudi Arabia", "passport_number": "EP123456", "status": "approved"},
    {"country": "Turkey", "passport_number": "EP654321", "status": "approved"},
    {"country": "UAE", "passport_number": "EP987654", "status": "submitted"},
    {"country": "Saudi Arabia", "passport_number": "EP456789", "status": "pending"},
    {"country": "United Kingdom", "passport_number": "EP000111", "status": "rejected"},
]
for data in visas_data:
    VisaApplication.objects.create(user=agent, **data)
print(f"Seeded {len(visas_data)} visa applications.")

# Seed Flight Quote Requests
flights_data = [
    {"departure_city": "Lahore", "destination_city": "Jeddah", "departure_date": datetime.date(2026, 8, 10), "return_date": datetime.date(2026, 8, 25), "status": "booked", "price_quote": 165000.00},
    {"departure_city": "Karachi", "destination_city": "Istanbul", "departure_date": datetime.date(2026, 9, 5), "return_date": datetime.date(2026, 9, 15), "status": "quoted", "price_quote": 125000.00},
    {"departure_city": "Islamabad", "destination_city": "Dubai", "departure_date": datetime.date(2026, 8, 20), "return_date": datetime.date(2026, 8, 30), "status": "pending", "price_quote": 85000.00},
    {"departure_city": "Lahore", "destination_city": "London", "departure_date": datetime.date(2026, 10, 1), "return_date": datetime.date(2026, 10, 15), "status": "quoted", "price_quote": 245000.00},
    {"departure_city": "Faisalabad", "destination_city": "Medina", "departure_date": datetime.date(2026, 8, 15), "return_date": None, "status": "cancelled", "price_quote": None},
    {"departure_city": "Sialkot", "destination_city": "Jeddah", "departure_date": datetime.date(2026, 9, 1), "return_date": datetime.date(2026, 9, 15), "status": "pending", "price_quote": None},
]
for data in flights_data:
    FlightQuoteRequest.objects.create(user=agent, **data)
print(f"Seeded {len(flights_data)} flight quotes.")

print("\nAll seeding operations completed successfully!")
