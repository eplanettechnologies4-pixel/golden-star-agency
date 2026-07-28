import sys
import os
import random
import datetime

# Add core_admin folder to sys.path so we can import django settings correctly
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.packages.models import Package
from apps.bookings.models import Booking
from apps.visa.models import VisaApplication
from apps.flights.models import FlightQuoteRequest

# Clean existing records (except superuser admin)
print("Cleaning old records...")
Booking.objects.all().delete()
VisaApplication.objects.all().delete()
FlightQuoteRequest.objects.all().delete()
Package.objects.all().delete()

# Keep superuser admin, delete other users
User.objects.filter(is_superuser=False).delete()

# Create B2B Agent Partner Users
print("Creating dummy Agent Partner users...")
agents_data = [
    {'username': 'karachi_travels', 'first_name': 'Zubair', 'last_name': 'Ahmed', 'company_name': 'Karachi Travel Solutions', 'approval_status': 'approved'},
    {'username': 'lahore_tours', 'first_name': 'Mansoor', 'last_name': 'Khan', 'company_name': 'Lahore Express Tour Op', 'approval_status': 'approved'},
    {'username': 'islamabad_pilgrims', 'first_name': 'Aisha', 'last_name': 'Siddiqua', 'company_name': 'Islamabad Pilgrim Services', 'approval_status': 'approved'},
    {'username': 'peshawar_wanderers', 'first_name': 'Fazal', 'last_name': 'Rahman', 'company_name': 'Khyber Travel & Tourism', 'approval_status': 'pending'},
    {'username': 'multan_ventures', 'first_name': 'Imran', 'last_name': 'Shah', 'company_name': 'Multan Sufi Journeys', 'approval_status': 'suspended'},
]

agents = []
for index, ad in enumerate(agents_data):
    user = User.objects.create_user(
        username=ad['username'],
        password='password123',
        email=f"{ad['username']}@example.com",
        first_name=ad['first_name'],
        last_name=ad['last_name'],
        role='agent',
        company_name=ad['company_name'],
        approval_status=ad['approval_status'],
        is_email_verified=True,
        phone=f"+92300123456{index}"
    )
    agents.append(user)

# Create Customer Users
print("Creating dummy Customer users...")
customers_data = [
    {'username': 'customer_ali', 'first_name': 'Ali', 'last_name': 'Raza'},
    {'username': 'customer_fatima', 'first_name': 'Fatima', 'last_name': 'Zahra'},
    {'username': 'customer_usman', 'first_name': 'Usman', 'last_name': 'Ghani'},
    {'username': 'customer_sana', 'first_name': 'Sana', 'last_name': 'Malik'},
]
customers = []
for index, cd in enumerate(customers_data):
    user = User.objects.create_user(
        username=cd['username'],
        password='password123',
        email=f"{cd['username']}@example.com",
        first_name=cd['first_name'],
        last_name=cd['last_name'],
        role='customer',
        is_email_verified=True,
        phone=f"+92300765432{index}"
    )
    customers.append(user)

# Create Travel Packages
print("Creating central travel packages...")
packages_data = [
    {'title': '5-Star Premium Hajj Package', 'description': '15 Days VIP Hajj journey with accommodation in Makkah clock tower and luxury tent in Mina.', 'price': 1250000.00, 'category': 'Hajj', 'duration_days': 15},
    {'title': 'Standard Economy Hajj Package', 'description': '21 Days budget-friendly Hajj packages with building accommodation and standard services.', 'price': 850000.00, 'category': 'Hajj', 'duration_days': 21},
    {'title': 'Premium 14-Days Umrah package', 'description': 'Elite 14 Days Umrah journey with 5-star hotels and luxury transport.', 'price': 350000.00, 'category': 'Umrah', 'duration_days': 14},
    {'title': 'Super Saver 10-Days Umrah package', 'description': 'Affordable 10 Days Umrah package with standard services near Haram.', 'price': 195000.00, 'category': 'Umrah', 'duration_days': 10},
    {'title': 'Turkey Highlights Group Tour', 'description': '7 Days group holiday covering Istanbul, Cappadocia, and Antalya.', 'price': 285000.00, 'category': 'Tour', 'duration_days': 7},
    {'title': 'Baku Explorer Family Package', 'description': '5 Days tour of Baku, Azerbaijan with visa and daily guided excursions.', 'price': 180000.00, 'category': 'Tour', 'duration_days': 5},
]
packages = []
for pd in packages_data:
    package = Package.objects.create(
        title=pd['title'],
        description=pd['description'],
        price=pd['price'],
        category=pd['category'],
        duration_days=pd['duration_days']
    )
    packages.append(package)

# Seed Bookings
print("Seeding bookings...")
booking_statuses = ['pending', 'confirmed', 'cancelled']
for agent in agents:
    # 2 bookings per agent
    for i in range(2):
        pkg = random.choice(packages)
        Booking.objects.create(
            user=agent,
            package=pkg,
            booking_type='package',
            status=random.choice(booking_statuses),
            total_price=pkg.price
        )
for customer in customers:
    pkg = random.choice(packages)
    Booking.objects.create(
        user=customer,
        package=pkg,
        booking_type='package',
        status='confirmed',
        total_price=pkg.price
    )

# Seed Visa Applications
print("Seeding visa applications...")
countries = ['Saudi Arabia', 'Turkey', 'Azerbaijan', 'Malaysia', 'United Arab Emirates']
visa_statuses = ['pending', 'submitted', 'approved', 'rejected']
for agent in agents:
    VisaApplication.objects.create(
        user=agent,
        country=random.choice(countries),
        passport_number=f"PK{random.randint(1000000, 9999999)}",
        status=random.choice(visa_statuses)
    )
for customer in customers:
    VisaApplication.objects.create(
        user=customer,
        country=random.choice(countries),
        passport_number=f"PK{random.randint(1000000, 9999999)}",
        status='approved'
    )

# Seed Flight Quote Requests
print("Seeding flight quote requests...")
cities = ['Karachi', 'Lahore', 'Islamabad', 'Jeddah', 'Istanbul', 'Baku', 'Kuala Lumpur']
flight_statuses = ['pending', 'quoted', 'booked', 'cancelled']
for agent in agents:
    dep = random.choice(cities)
    dest = random.choice([c for c in cities if c != dep])
    FlightQuoteRequest.objects.create(
        user=agent,
        departure_city=dep,
        destination_city=dest,
        departure_date=datetime.date.today() + datetime.timedelta(days=random.randint(15, 60)),
        status=random.choice(flight_statuses),
        price_quote=random.choice([None, 125000.00, 185000.00, 240000.00])
    )
for customer in customers:
    dep = random.choice(cities)
    dest = random.choice([c for c in cities if c != dep])
    FlightQuoteRequest.objects.create(
        user=customer,
        departure_city=dep,
        destination_city=dest,
        departure_date=datetime.date.today() + datetime.timedelta(days=random.randint(10, 45)),
        status='quoted',
        price_quote=195000.00
    )

print("Dummy real-time stats and metrics data seeded successfully!")
