import os
import sys
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.airline_ticketing.models import AgentPackage

def create_umrah_packages():
    print("Creating new rich B2B Wholesale Umrah Packages with real-time flight itineraries & baggage details...")

    # Package 1: 15-Day Direct Saudi Airlines Umrah Package
    pkg1, created = AgentPackage.objects.update_or_create(
        title="15-Day Premium Direct Umrah Group Deal 2026",
        defaults={
            'package_type': 'umrah',
            'description': 'VIP 15-Day Umrah Package with 5-Star luxury hotels in Makkah & Madinah, direct Saudi Airlines flight, full board meals, and complete guided Ziyarat.',
            'duration_days': 15,
            'agent_price': 225000.00,
            'adult_price': 225000.00,
            'child_price': 195000.00,
            'infant_price': 65000.00,
            'price_sharing': 195000.00,
            'price_quad': 210000.00,
            'price_triple': 225000.00,
            'price_double': 250000.00,
            'departure_date': date.today() + timedelta(days=10),
            'return_date': date.today() + timedelta(days=25),
            'makkah_hotel_name': "Swissotel Makkah (Clock Tower)",
            'makkah_hotel_distance': "0m from Haram",
            'makkah_nights': 8,
            'madinah_hotel_name': "Pullman Zamzam Madinah",
            'madinah_hotel_distance': "150m from Haram",
            'madinah_nights': 7,
            'flight_name': "Saudi Airlines",
            'flight_route_type': "direct",
            'flight_route': "LHE - JED - MED - LHE",
            'baggage_detail': "30 KG Check-in + 7 KG Hand Carry",
            'sectors_data': [
                {
                    'from': 'LHE (Lahore)',
                    'to': 'JED (Jeddah)',
                    'flight_no': 'SV-738',
                    'dep_time': '14:30 PM',
                    'arr_time': '18:30 PM',
                    'baggage': '30 KG Check-in'
                },
                {
                    'from': 'MED (Madinah)',
                    'to': 'LHE (Lahore)',
                    'flight_no': 'SV-739',
                    'dep_time': '09:00 AM',
                    'arr_time': '15:00 PM',
                    'baggage': '30 KG Check-in'
                }
            ],
            'includes_meal': True,
            'meal_detail': "Full Board Buffet",
            'transport_type': "Private VIP GMC Bus",
            'total_seats': 40,
            'booked_seats': 8,
            'is_active': True,
        }
    )
    print(f"Created/Updated: {pkg1.title} (Created: {created})")

    # Package 2: 21-Day Emirates Connecting Flight Umrah Deal
    pkg2, created = AgentPackage.objects.update_or_create(
        title="21-Day Executive Connecting Umrah Package (Emirates via Dubai)",
        defaults={
            'package_type': 'umrah',
            'description': '21-Day Luxury Umrah Group deal flying Emirates via Dubai connection. Frontline 5-Star accommodations with shuttle transfers and guided historical Ziyarat tours.',
            'duration_days': 21,
            'agent_price': 275000.00,
            'adult_price': 275000.00,
            'child_price': 235000.00,
            'infant_price': 75000.00,
            'price_sharing': 240000.00,
            'price_quad': 255000.00,
            'price_triple': 275000.00,
            'price_double': 310000.00,
            'departure_date': date.today() + timedelta(days=15),
            'return_date': date.today() + timedelta(days=36),
            'makkah_hotel_name': "Makkah Hotel & Towers",
            'makkah_hotel_distance': "100m from Haram",
            'makkah_nights': 11,
            'madinah_hotel_name': "Anwar Al Madinah Movenpick",
            'madinah_hotel_distance': "50m from Haram",
            'madinah_nights': 10,
            'flight_name': "Emirates Airline",
            'flight_route_type': "via",
            'flight_route': "KHI - DXB - JED - MED - DXB - KHI",
            'baggage_detail': "2x23 KG Check-in + 7 KG Hand",
            'sectors_data': [
                {
                    'from': 'KHI (Karachi)',
                    'to': 'DXB (Dubai)',
                    'flight_no': 'EK-609',
                    'dep_time': '12:00 PM',
                    'arr_time': '13:15 PM',
                    'baggage': '2x23 KG Check-in'
                },
                {
                    'from': 'DXB (Dubai)',
                    'to': 'JED (Jeddah)',
                    'flight_no': 'EK-801',
                    'dep_time': '16:30 PM',
                    'arr_time': '18:30 PM',
                    'baggage': '2x23 KG Check-in'
                },
                {
                    'from': 'MED (Madinah)',
                    'to': 'DXB (Dubai)',
                    'flight_no': 'EK-802',
                    'dep_time': '10:00 AM',
                    'arr_time': '13:30 PM',
                    'baggage': '2x23 KG Check-in'
                },
                {
                    'from': 'DXB (Dubai)',
                    'to': 'KHI (Karachi)',
                    'flight_no': 'EK-610',
                    'dep_time': '16:00 PM',
                    'arr_time': '19:00 PM',
                    'baggage': '2x23 KG Check-in'
                }
            ],
            'includes_meal': True,
            'meal_detail': "Half Board Buffet",
            'transport_type': "Luxury Coaster",
            'total_seats': 50,
            'booked_seats': 15,
            'is_active': True,
        }
    )
    print(f"Created/Updated: {pkg2.title} (Created: {created})")

    # Package 3: 10-Day Super Economy Umrah Saver
    pkg3, created = AgentPackage.objects.update_or_create(
        title="10-Day Super Saver Umrah Package (Flynas Direct)",
        defaults={
            'package_type': 'umrah',
            'description': '10-Day Economy Umrah package ideal for quick pilgrimage trips. Clean 4-star hotels with shuttle service and direct Flynas flights.',
            'duration_days': 10,
            'agent_price': 145000.00,
            'adult_price': 145000.00,
            'child_price': 125000.00,
            'infant_price': 45000.00,
            'price_sharing': 130000.00,
            'price_quad': 145000.00,
            'price_triple': 158000.00,
            'price_double': 175000.00,
            'departure_date': date.today() + timedelta(days=5),
            'return_date': date.today() + timedelta(days=15),
            'makkah_hotel_name': "Kiswah Towers Makkah",
            'makkah_hotel_distance': "900m (24/7 Shuttle)",
            'makkah_nights': 5,
            'madinah_hotel_name': "Emaar Elite Madinah",
            'madinah_hotel_distance': "350m from Haram",
            'madinah_nights': 5,
            'flight_name': "Flynas",
            'flight_route_type': "direct",
            'flight_route': "ISB - JED - MED - ISB",
            'baggage_detail': "20 KG Check-in + 7 KG Hand",
            'sectors_data': [
                {
                    'from': 'ISB (Islamabad)',
                    'to': 'JED (Jeddah)',
                    'flight_no': 'XY-312',
                    'dep_time': '03:30 AM',
                    'arr_time': '07:15 AM',
                    'baggage': '20 KG Check-in'
                },
                {
                    'from': 'MED (Madinah)',
                    'to': 'ISB (Islamabad)',
                    'flight_no': 'XY-313',
                    'dep_time': '11:00 AM',
                    'arr_time': '17:45 PM',
                    'baggage': '20 KG Check-in'
                }
            ],
            'includes_meal': False,
            'meal_detail': "Room Only",
            'transport_type': "Sharing Bus",
            'total_seats': 35,
            'booked_seats': 2,
            'is_active': True,
        }
    )
    print(f"Created/Updated: {pkg3.title} (Created: {created})")

if __name__ == '__main__':
    create_umrah_packages()
