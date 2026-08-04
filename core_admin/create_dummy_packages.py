import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.airline_ticketing.models import AgentPackage, AgentHajjPackage, AgentHajjAccommodation

def create_dummy_data():
    print("Creating dummy Umrah & Hajj wholesale packages...")

    # 1. Dummy Umrah Package 1
    u1, created = AgentPackage.objects.get_or_create(
        title="15-Day Executive Wholesale Umrah Package",
        defaults={
            'description': "VIP 15 Days Umrah Package including 5-Star Makkah & Madinah Hotels, Quad/Triple/Double options, Direct Saudi Airlines Flight, Full Board Meals, and Ziyarat.",
            'package_type': 'umrah',
            'duration_days': 15,
            'agent_price': 210000.00,
            'adult_price': 210000.00,
            'child_price': 180000.00,
            'infant_price': 65000.00,
            'price_sharing': 185000.00,
            'price_quad': 195000.00,
            'price_triple': 210000.00,
            'price_double': 235000.00,
            'makkah_hotel_name': "Swissotel Makkah (Clock Tower)",
            'makkah_hotel_distance': "Zero meters from Haram",
            'makkah_nights': 7,
            'madinah_hotel_name': "Pullman Zamzam Madinah",
            'madinah_hotel_distance': "150 meters from Masjid an-Nabawi",
            'madinah_nights': 7,
            'flight_name': "Saudi Airlines",
            'flight_route_type': "direct",
            'flight_route': "KHI - JED - MED - KHI",
            'includes_meal': True,
            'meal_detail': "Full Board Buffet",
            'transport_type': "Private GMC Bus",
            'total_seats': 30,
            'booked_seats': 5,
            'is_active': True,
        }
    )
    print(f"Umrah Package 1: {u1.title} (Created: {created})")

    # 2. Dummy Umrah Package 2
    u2, created = AgentPackage.objects.get_or_create(
        title="21-Day Economy Plus Umrah Group Deal",
        defaults={
            'description': "21 Days Economy Umrah Package with 24/7 shuttle service hotels, direct flights, and complete guided Ziyarat.",
            'package_type': 'umrah',
            'duration_days': 21,
            'agent_price': 165000.00,
            'adult_price': 165000.00,
            'child_price': 145000.00,
            'infant_price': 55000.00,
            'price_sharing': 150000.00,
            'price_quad': 165000.00,
            'price_triple': 178000.00,
            'price_double': 195000.00,
            'makkah_hotel_name': "Kiswah Towers Makkah",
            'makkah_hotel_distance': "900 meters (24/7 Shuttle)",
            'makkah_nights': 11,
            'madinah_hotel_name': "Emaar Elite Madinah",
            'madinah_hotel_distance': "400 meters from Haram",
            'madinah_nights': 9,
            'flight_name': "PIA Airblue",
            'flight_route_type': "direct",
            'flight_route': "LHR - JED - MED - LHR",
            'includes_meal': True,
            'meal_detail': "Half Board",
            'transport_type': "Sharing Coaster",
            'total_seats': 45,
            'booked_seats': 12,
            'is_active': True,
        }
    )
    print(f"Umrah Package 2: {u2.title} (Created: {created})")

    # 3. Dummy Hajj Package 1
    h1, created = AgentHajjPackage.objects.get_or_create(
        title="Executive 25-Day Non-Shifting Hajj Package 2026",
        defaults={
            'description': "5-Star Non-Shifting Luxury Hajj package with frontline Clock Tower accommodation in Makkah and Markazia hotel in Madinah, Maktab 1 VIP Mina Tents, and full guidance.",
            'duration_days': 25,
            'price_quad': 1350000.00,
            'price_triple': 1480000.00,
            'price_double': 1650000.00,
            'price_sharing': 1250000.00,
            'hajj_operator_name': "Al-Harmain Hajj & Umrah Services Pvt Ltd",
            'license_number': "HGO-4092",
            'saudi_registration_number': "KSA-HAJJ-9921",
            'airline_name': "Saudi Airlines",
            'flight_route': "KHI - JED - MED - KHI",
            'includes_meal': True,
            'meal_detail': "Full Board Buffet & Mina VIP Catering",
            'makkah_hotel_name': "Makkah Construction Hotel (Frontline)",
            'makkah_hotel_distance': "Zero meters from Haram",
            'madinah_hotel_name': "Dar Al Taqwa Madinah",
            'madinah_hotel_distance': "50 meters from Nabawi",
            'total_seats': 25,
            'available_seats': 25,
            'is_active': True,
        }
    )
    print(f"Hajj Package 1: {h1.title} (Created: {created})")

    if created:
        AgentHajjAccommodation.objects.create(
            agent_hajj_package=h1,
            city='makkah',
            manual_hotel_name="Makkah Construction Hotel (Frontline)",
            manual_hotel_distance="Zero meters from Haram",
            nights=14,
            order=0
        )
        AgentHajjAccommodation.objects.create(
            agent_hajj_package=h1,
            city='madinah',
            manual_hotel_name="Dar Al Taqwa Madinah",
            manual_hotel_distance="50 meters from Nabawi",
            nights=10,
            order=1
        )

    # 4. Dummy Hajj Package 2
    h2, created = AgentHajjPackage.objects.get_or_create(
        title="Standard 35-Day Shifting Hajj Wholesale Package",
        defaults={
            'description': "Comprehensive 35-Day Shifting Hajj deal featuring Azizia building stay during peak Hajj days, Central Madinah hotel stay, Air-conditioned Mina/Arafat tents, and full support.",
            'duration_days': 35,
            'price_quad': 1050000.00,
            'price_triple': 1150000.00,
            'price_double': 1280000.00,
            'price_sharing': 980000.00,
            'hajj_operator_name': "Labbaik Global Travel Operator",
            'license_number': "HGO-2815",
            'saudi_registration_number': "KSA-HAJJ-3310",
            'airline_name': "PIA Special Hajj Flight",
            'flight_route': "ISB - JED - MED - ISB",
            'includes_meal': True,
            'meal_detail': "Full Board 3 Times Daily",
            'makkah_hotel_name': "Azizia Shifting Building / Dar Al Eiman",
            'makkah_hotel_distance': "Shifting Building + Central Makkah Hotel",
            'madinah_hotel_name': "Al Nokhba Royal Care Madinah",
            'madinah_hotel_distance': "250 meters from Nabawi",
            'total_seats': 40,
            'available_seats': 38,
            'is_active': True,
        }
    )
    print(f"Hajj Package 2: {h2.title} (Created: {created})")

    if created:
        AgentHajjAccommodation.objects.create(
            agent_hajj_package=h2,
            city='makkah',
            manual_hotel_name="Azizia Shifting Building / Dar Al Eiman",
            manual_hotel_distance="Shifting Building + Central Makkah Hotel",
            nights=20,
            order=0
        )
        AgentHajjAccommodation.objects.create(
            agent_hajj_package=h2,
            city='madinah',
            manual_hotel_name="Al Nokhba Royal Care Madinah",
            manual_hotel_distance="250 meters from Nabawi",
            nights=14,
            order=1
        )

    print("Dummy Umrah & Hajj packages created successfully!")

if __name__ == '__main__':
    create_dummy_data()
