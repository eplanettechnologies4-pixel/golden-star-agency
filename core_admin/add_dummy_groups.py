import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.airline_ticketing.models import GroupFarePolicy, Airline
from decimal import Decimal

def create_dummy_group_tickets():
    # Remove existing dummy test policies if present to replace cleanly
    GroupFarePolicy.objects.filter(airline_name_custom__icontains='Air').delete()

    saudia = Airline.objects.filter(name__icontains='Saudia').first() or Airline.objects.first()
    pia = Airline.objects.filter(name__icontains='PIA').first() or Airline.objects.first()
    airblue = Airline.objects.filter(name__icontains='AirBlue').first() or Airline.objects.first()
    emirates = Airline.objects.filter(name__icontains='Emirates').first() or Airline.objects.first()

    dummy_tickets = [
        # Ticket 1: One Way + Direct (1 Sector: LHE ➔ JED)
        {
            "airline": saudia,
            "airline_name_custom": "Saudi Arabian Airlines",
            "departure_city": "Lahore (LHE)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "03:30 AM",
            "arrival_time": "06:45 AM",
            "trip_type": "oneway",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 60,
            "available_seats": 45,
            "min_group_size": 10,
            "discount_type": "flat",
            "discount_value": Decimal("7000.00"),
            "baggage_weight_kg": 30,
            "return_baggage_weight_kg": 0,
            "base_fare": Decimal("85000.00"),
            "group_fare_override": Decimal("78000.00"),
            "is_active": True,
            "route_sectors": [
                {
                    "from_city": "Lahore (LHE)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "SV-733",
                    "flight_date": "10 AUG",
                    "dep_time": "03:30 AM",
                    "arr_time": "06:45 AM"
                }
            ]
        },

        # Ticket 2: Round Trip + Direct (2 Sectors: LHE ➔ JED, JED ➔ LHE)
        {
            "airline": pia,
            "airline_name_custom": "PIA - Pakistan International Airlines",
            "departure_city": "Lahore (LHE)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "09:00 AM",
            "arrival_time": "01:30 PM",
            "return_departure_time": "04:00 PM",
            "return_arrival_time": "10:30 PM",
            "trip_type": "return",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 80,
            "available_seats": 60,
            "min_group_size": 15,
            "discount_type": "flat",
            "discount_value": Decimal("13000.00"),
            "baggage_weight_kg": 35,
            "return_baggage_weight_kg": 35,
            "base_fare": Decimal("165000.00"),
            "group_fare_override": Decimal("152000.00"),
            "is_active": True,
            "route_sectors": [
                {
                    "from_city": "Lahore (LHE)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "PK-759",
                    "flight_date": "15 SEP",
                    "dep_time": "09:00 AM",
                    "arr_time": "01:30 PM"
                },
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Lahore (LHE)",
                    "flight_no": "PK-760",
                    "flight_date": "30 SEP",
                    "dep_time": "04:00 PM",
                    "arr_time": "10:30 PM"
                }
            ]
        },

        # Ticket 3: One Way + Via Flight (2 Sectors: LYP ➔ SHJ, SHJ ➔ JED)
        {
            "airline": airblue,
            "airline_name_custom": "Air Arabia",
            "departure_city": "Faisalabad (LYP)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "02:15 AM",
            "arrival_time": "08:45 AM",
            "trip_type": "oneway",
            "route_type": "via",
            "via_city": "Sharjah (SHJ)",
            "has_meal": True,
            "total_seats": 50,
            "available_seats": 35,
            "min_group_size": 10,
            "discount_type": "flat",
            "discount_value": Decimal("10000.00"),
            "baggage_weight_kg": 30,
            "return_baggage_weight_kg": 0,
            "base_fare": Decimal("95000.00"),
            "group_fare_override": Decimal("85000.00"),
            "is_active": True,
            "route_sectors": [
                {
                    "from_city": "Faisalabad (LYP)",
                    "to_city": "Sharjah (SHJ)",
                    "flight_no": "G9-542",
                    "flight_date": "20 OCT",
                    "dep_time": "02:15 AM",
                    "arr_time": "04:30 AM"
                },
                {
                    "from_city": "Sharjah (SHJ)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "G9-115",
                    "flight_date": "20 OCT",
                    "dep_time": "06:15 AM",
                    "arr_time": "08:45 AM"
                }
            ]
        },

        # Ticket 4: Round Trip + Via Flight (4 Sectors: LYP ➔ SHJ, SHJ ➔ JED, JED ➔ SHJ, SHJ ➔ LYP)
        {
            "airline": emirates,
            "airline_name_custom": "Air Arabia Roundtrip",
            "departure_city": "Faisalabad (LYP)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "02:15 AM",
            "arrival_time": "08:45 AM",
            "return_departure_time": "01:00 PM",
            "return_arrival_time": "09:30 PM",
            "trip_type": "return",
            "route_type": "via",
            "via_city": "Sharjah (SHJ)",
            "has_meal": True,
            "total_seats": 70,
            "available_seats": 52,
            "min_group_size": 15,
            "discount_type": "flat",
            "discount_value": Decimal("18000.00"),
            "baggage_weight_kg": 35,
            "return_baggage_weight_kg": 35,
            "base_fare": Decimal("175000.00"),
            "group_fare_override": Decimal("157000.00"),
            "is_active": True,
            "route_sectors": [
                # 2 Outbound Sectors
                {
                    "from_city": "Faisalabad (LYP)",
                    "to_city": "Sharjah (SHJ)",
                    "flight_no": "G9-542",
                    "flight_date": "05 NOV",
                    "dep_time": "02:15 AM",
                    "arr_time": "04:30 AM"
                },
                {
                    "from_city": "Sharjah (SHJ)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "G9-115",
                    "flight_date": "05 NOV",
                    "dep_time": "06:15 AM",
                    "arr_time": "08:45 AM"
                },
                # 2 Return Sectors
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Sharjah (SHJ)",
                    "flight_no": "G9-116",
                    "flight_date": "20 NOV",
                    "dep_time": "01:00 PM",
                    "arr_time": "04:30 PM"
                },
                {
                    "from_city": "Sharjah (SHJ)",
                    "to_city": "Faisalabad (LYP)",
                    "flight_no": "G9-543",
                    "flight_date": "20 NOV",
                    "dep_time": "06:45 PM",
                    "arr_time": "09:30 PM"
                }
            ]
        }
    ]

    created = 0
    for t_data in dummy_tickets:
        policy = GroupFarePolicy.objects.create(**t_data)
        created += 1
        print(f"Created Group Ticket #{policy.id}: {policy.airline_name_custom} ({policy.trip_type} / {policy.route_type}) - {len(policy.route_sectors)} Sectors")

    print(f"Successfully generated {created} updated group tickets!")

if __name__ == '__main__':
    create_dummy_group_tickets()
