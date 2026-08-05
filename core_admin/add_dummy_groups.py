import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.airline_ticketing.models import GroupFarePolicy, Airline
from decimal import Decimal

def create_dummy_group_tickets():
    saudia = Airline.objects.filter(name__icontains='Saudia').first() or Airline.objects.first()
    pia = Airline.objects.filter(name__icontains='PIA').first() or Airline.objects.first()
    qatar = Airline.objects.filter(name__icontains='Qatar').first() or Airline.objects.first()
    emirates = Airline.objects.filter(name__icontains='Emirates').first() or Airline.objects.first()

    dummy_tickets = [
        # Ticket 1: One Way + Direct (2 Sectors)
        {
            "airline": saudia,
            "airline_name_custom": "Saudi Arabian Airlines (Saudia)",
            "departure_city": "Karachi (KHI)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "03:30 AM",
            "arrival_time": "06:45 AM",
            "trip_type": "oneway",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 60,
            "available_seats": 42,
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
                    "from_city": "Karachi (KHI)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "SV-701",
                    "flight_date": "10 AUG",
                    "dep_time": "03:30 AM",
                    "arr_time": "06:45 AM"
                },
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Jeddah Terminal 1",
                    "flight_no": "SV-701",
                    "flight_date": "10 AUG",
                    "dep_time": "06:45 AM",
                    "arr_time": "07:15 AM"
                }
            ]
        },

        # Ticket 2: Round Trip + Direct (4 Sectors)
        {
            "airline": pia,
            "airline_name_custom": "PIA - Pakistan International Airlines",
            "departure_city": "Lahore (LHE)",
            "destination_city": "Medina (MED)",
            "departure_time": "09:00 AM",
            "arrival_time": "01:30 PM",
            "return_departure_time": "04:00 PM",
            "return_arrival_time": "10:30 PM",
            "trip_type": "return",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 80,
            "available_seats": 65,
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
                    "to_city": "Medina (MED)",
                    "flight_no": "PK-743",
                    "flight_date": "15 SEP",
                    "dep_time": "09:00 AM",
                    "arr_time": "01:30 PM"
                },
                {
                    "from_city": "Medina (MED)",
                    "to_city": "MED Terminal Arrival",
                    "flight_no": "PK-743",
                    "flight_date": "15 SEP",
                    "dep_time": "01:30 PM",
                    "arr_time": "02:00 PM"
                },
                {
                    "from_city": "Medina (MED)",
                    "to_city": "Lahore (LHE)",
                    "flight_no": "PK-744",
                    "flight_date": "30 SEP",
                    "dep_time": "04:00 PM",
                    "arr_time": "10:30 PM"
                },
                {
                    "from_city": "Lahore (LHE)",
                    "to_city": "LHE Main Gate",
                    "flight_no": "PK-744",
                    "flight_date": "30 SEP",
                    "dep_time": "10:30 PM",
                    "arr_time": "11:00 PM"
                }
            ]
        },

        # Ticket 3: One Way + Via Connection (4 Sectors)
        {
            "airline": qatar,
            "airline_name_custom": "Qatar Airways",
            "departure_city": "Islamabad (ISB)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "02:15 AM",
            "arrival_time": "11:15 AM",
            "trip_type": "oneway",
            "route_type": "via",
            "via_city": "Doha (DOH) - Riyadh (RUH)",
            "has_meal": True,
            "total_seats": 50,
            "available_seats": 38,
            "min_group_size": 10,
            "discount_type": "flat",
            "discount_value": Decimal("12000.00"),
            "baggage_weight_kg": 40,
            "return_baggage_weight_kg": 0,
            "base_fare": Decimal("110000.00"),
            "group_fare_override": Decimal("98000.00"),
            "is_active": True,
            "route_sectors": [
                {
                    "from_city": "Islamabad (ISB)",
                    "to_city": "Doha (DOH)",
                    "flight_no": "QR-633",
                    "flight_date": "20 OCT",
                    "dep_time": "02:15 AM",
                    "arr_time": "04:30 AM"
                },
                {
                    "from_city": "Doha Transit",
                    "to_city": "DOH Gate B",
                    "flight_no": "QR-Transit",
                    "flight_date": "20 OCT",
                    "dep_time": "04:30 AM",
                    "arr_time": "06:00 AM"
                },
                {
                    "from_city": "Doha (DOH)",
                    "to_city": "Riyadh (RUH)",
                    "flight_no": "QR-1165",
                    "flight_date": "20 OCT",
                    "dep_time": "06:00 AM",
                    "arr_time": "07:45 AM"
                },
                {
                    "from_city": "Riyadh (RUH)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "SV-1020",
                    "flight_date": "20 OCT",
                    "dep_time": "09:30 AM",
                    "arr_time": "11:15 AM"
                }
            ]
        },

        # Ticket 4: Round Trip + Via Connection (8 Sectors)
        {
            "airline": emirates,
            "airline_name_custom": "Emirates & Oman Air",
            "departure_city": "Karachi (KHI)",
            "destination_city": "Medina (MED)",
            "departure_time": "08:30 AM",
            "arrival_time": "09:00 AM (+1)",
            "return_departure_time": "02:00 PM",
            "return_arrival_time": "07:45 AM (+1)",
            "trip_type": "return",
            "route_type": "via",
            "via_city": "Dubai (DXB) - Muscat (MCT) - Jeddah (JED)",
            "has_meal": True,
            "total_seats": 100,
            "available_seats": 78,
            "min_group_size": 20,
            "discount_type": "flat",
            "discount_value": Decimal("21000.00"),
            "baggage_weight_kg": 40,
            "return_baggage_weight_kg": 40,
            "base_fare": Decimal("210000.00"),
            "group_fare_override": Decimal("189000.00"),
            "is_active": True,
            "route_sectors": [
                # 4 Outbound Sectors
                {
                    "from_city": "Karachi (KHI)",
                    "to_city": "Dubai (DXB)",
                    "flight_no": "EK-609",
                    "flight_date": "05 NOV",
                    "dep_time": "08:30 AM",
                    "arr_time": "10:45 AM"
                },
                {
                    "from_city": "Dubai (DXB)",
                    "to_city": "Muscat (MCT)",
                    "flight_no": "EK-862",
                    "flight_date": "05 NOV",
                    "dep_time": "01:15 PM",
                    "arr_time": "02:30 PM"
                },
                {
                    "from_city": "Muscat (MCT)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "WY-671",
                    "flight_date": "05 NOV",
                    "dep_time": "04:00 PM",
                    "arr_time": "06:45 PM"
                },
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Medina (MED)",
                    "flight_no": "SV-1430",
                    "flight_date": "06 NOV",
                    "dep_time": "08:00 AM",
                    "arr_time": "09:00 AM"
                },
                # 4 Return Sectors
                {
                    "from_city": "Medina (MED)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "SV-1431",
                    "flight_date": "20 NOV",
                    "dep_time": "02:00 PM",
                    "arr_time": "03:00 PM"
                },
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Muscat (MCT)",
                    "flight_no": "WY-672",
                    "flight_date": "20 NOV",
                    "dep_time": "05:30 PM",
                    "arr_time": "09:15 PM"
                },
                {
                    "from_city": "Muscat (MCT)",
                    "to_city": "Dubai (DXB)",
                    "flight_no": "EK-863",
                    "flight_date": "21 NOV",
                    "dep_time": "01:00 AM",
                    "arr_time": "02:15 AM"
                },
                {
                    "from_city": "Dubai (DXB)",
                    "to_city": "Karachi (KHI)",
                    "flight_no": "EK-608",
                    "flight_date": "21 NOV",
                    "dep_time": "04:30 AM",
                    "arr_time": "07:45 AM"
                }
            ]
        }
    ]

    created = 0
    for t_data in dummy_tickets:
        policy = GroupFarePolicy.objects.create(**t_data)
        created += 1
        print(f"Created Group Ticket #{policy.id}: {policy.airline_name_custom} ({policy.trip_type} / {policy.route_type}) - {len(policy.route_sectors)} Sectors")

    print(f"Successfully added {created} dummy group tickets!")

if __name__ == '__main__':
    create_dummy_group_tickets()
