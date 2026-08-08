import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.airline_ticketing.models import GroupFarePolicy, Airline
from decimal import Decimal

def seed_10_group_tickets():
    # Clear existing policies to seed clean 10 group tickets
    GroupFarePolicy.objects.all().delete()

    saudia = Airline.objects.filter(name__icontains='Saudia').first() or Airline.objects.first()

    group_tickets_data = [
        # 1. Saudi Arabian Airlines - LHE ➔ JED (Direct Round Trip)
        {
            "airline": saudia,
            "airline_name_custom": "Saudi Arabian Airlines",
            "departure_city": "Lahore (LHE)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "03:30 AM",
            "arrival_time": "06:45 AM",
            "return_departure_time": "09:00 PM",
            "return_arrival_time": "03:30 AM",
            "trip_type": "return",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 60,
            "available_seats": 48,
            "min_group_size": 10,
            "discount_type": "flat",
            "discount_value": Decimal("17000.00"),
            "baggage_weight_kg": 35,
            "return_baggage_weight_kg": 35,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Lahore (LHE)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "SV-733",
                    "flight_date": "15 SEP",
                    "dep_time": "03:30 AM",
                    "arr_time": "06:45 AM"
                },
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Lahore (LHE)",
                    "flight_no": "SV-734",
                    "flight_date": "30 SEP",
                    "dep_time": "09:00 PM",
                    "arr_time": "03:30 AM"
                }
            ]
        },

        # 2. Emirates - ISB ➔ DXB (Direct Round Trip)
        {
            "airline": saudia,
            "airline_name_custom": "Emirates",
            "departure_city": "Islamabad (ISB)",
            "destination_city": "Dubai (DXB)",
            "departure_time": "03:10 AM",
            "arrival_time": "05:40 AM",
            "return_departure_time": "09:30 PM",
            "return_arrival_time": "01:50 AM",
            "trip_type": "return",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 75,
            "available_seats": 55,
            "min_group_size": 12,
            "discount_type": "flat",
            "discount_value": Decimal("13000.00"),
            "baggage_weight_kg": 30,
            "return_baggage_weight_kg": 30,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Islamabad (ISB)",
                    "to_city": "Dubai (DXB)",
                    "flight_no": "EK-613",
                    "flight_date": "20 SEP",
                    "dep_time": "03:10 AM",
                    "arr_time": "05:40 AM"
                },
                {
                    "from_city": "Dubai (DXB)",
                    "to_city": "Islamabad (ISB)",
                    "flight_no": "EK-614",
                    "flight_date": "05 OCT",
                    "dep_time": "09:30 PM",
                    "arr_time": "01:50 AM"
                }
            ]
        },

        # 3. Qatar Airways - KHI ➔ DOH ➔ JED (Via Round Trip)
        {
            "airline": saudia,
            "airline_name_custom": "Qatar Airways",
            "departure_city": "Karachi (KHI)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "04:30 AM",
            "arrival_time": "10:15 AM",
            "return_departure_time": "01:00 PM",
            "return_arrival_time": "09:45 PM",
            "trip_type": "return",
            "route_type": "via",
            "via_city": "Doha (DOH)",
            "has_meal": True,
            "total_seats": 80,
            "available_seats": 62,
            "min_group_size": 15,
            "discount_type": "flat",
            "discount_value": Decimal("20000.00"),
            "baggage_weight_kg": 40,
            "return_baggage_weight_kg": 40,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Karachi (KHI)",
                    "to_city": "Doha (DOH)",
                    "flight_no": "QR-605",
                    "flight_date": "25 SEP",
                    "dep_time": "04:30 AM",
                    "arr_time": "05:55 AM"
                },
                {
                    "from_city": "Doha (DOH)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "QR-1188",
                    "flight_date": "25 SEP",
                    "dep_time": "07:30 AM",
                    "arr_time": "10:15 AM"
                },
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Doha (DOH)",
                    "flight_no": "QR-1189",
                    "flight_date": "10 OCT",
                    "dep_time": "01:00 PM",
                    "arr_time": "03:20 PM"
                },
                {
                    "from_city": "Doha (DOH)",
                    "to_city": "Karachi (KHI)",
                    "flight_no": "QR-606",
                    "flight_date": "10 OCT",
                    "dep_time": "05:30 PM",
                    "arr_time": "09:45 PM"
                }
            ]
        },

        # 4. Flydubai - PEW ➔ DXB (Direct One Way)
        {
            "airline": saudia,
            "airline_name_custom": "Flydubai",
            "departure_city": "Peshawar (PEW)",
            "destination_city": "Dubai (DXB)",
            "departure_time": "11:20 AM",
            "arrival_time": "01:50 PM",
            "trip_type": "oneway",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 50,
            "available_seats": 40,
            "min_group_size": 8,
            "discount_type": "flat",
            "discount_value": Decimal("8000.00"),
            "baggage_weight_kg": 30,
            "return_baggage_weight_kg": 0,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Peshawar (PEW)",
                    "to_city": "Dubai (DXB)",
                    "flight_no": "FZ-338",
                    "flight_date": "28 SEP",
                    "dep_time": "11:20 AM",
                    "arr_time": "01:50 PM"
                }
            ]
        },

        # 5. Air Arabia - LYP ➔ SHJ ➔ MED (Via One Way)
        {
            "airline": saudia,
            "airline_name_custom": "Air Arabia",
            "departure_city": "Faisalabad (LYP)",
            "destination_city": "Madinah (MED)",
            "departure_time": "02:15 AM",
            "arrival_time": "08:45 AM",
            "trip_type": "oneway",
            "route_type": "via",
            "via_city": "Sharjah (SHJ)",
            "has_meal": True,
            "total_seats": 55,
            "available_seats": 38,
            "min_group_size": 10,
            "discount_type": "flat",
            "discount_value": Decimal("10000.00"),
            "baggage_weight_kg": 30,
            "return_baggage_weight_kg": 0,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Faisalabad (LYP)",
                    "to_city": "Sharjah (SHJ)",
                    "flight_no": "G9-542",
                    "flight_date": "02 OCT",
                    "dep_time": "02:15 AM",
                    "arr_time": "04:30 AM"
                },
                {
                    "from_city": "Sharjah (SHJ)",
                    "to_city": "Madinah (MED)",
                    "flight_no": "G9-115",
                    "flight_date": "02 OCT",
                    "dep_time": "06:15 AM",
                    "arr_time": "08:45 AM"
                }
            ]
        },

        # 6. PIA - MUX ➔ JED (Direct Round Trip)
        {
            "airline": saudia,
            "airline_name_custom": "PIA - Pakistan International Airlines",
            "departure_city": "Multan (MUX)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "08:30 AM",
            "arrival_time": "12:15 PM",
            "return_departure_time": "03:00 PM",
            "return_arrival_time": "09:30 PM",
            "trip_type": "return",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 90,
            "available_seats": 70,
            "min_group_size": 20,
            "discount_type": "flat",
            "discount_value": Decimal("15000.00"),
            "baggage_weight_kg": 35,
            "return_baggage_weight_kg": 35,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Multan (MUX)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "PK-739",
                    "flight_date": "08 OCT",
                    "dep_time": "08:30 AM",
                    "arr_time": "12:15 PM"
                },
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Multan (MUX)",
                    "flight_no": "PK-740",
                    "flight_date": "22 OCT",
                    "dep_time": "03:00 PM",
                    "arr_time": "09:30 PM"
                }
            ]
        },

        # 7. Flynas - SKT ➔ RUH (Direct One Way)
        {
            "airline": saudia,
            "airline_name_custom": "Flynas",
            "departure_city": "Sialkot (SKT)",
            "destination_city": "Riyadh (RUH)",
            "departure_time": "05:45 AM",
            "arrival_time": "08:30 AM",
            "trip_type": "oneway",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 45,
            "available_seats": 35,
            "min_group_size": 10,
            "discount_type": "flat",
            "discount_value": Decimal("9000.00"),
            "baggage_weight_kg": 30,
            "return_baggage_weight_kg": 0,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Sialkot (SKT)",
                    "to_city": "Riyadh (RUH)",
                    "flight_no": "XY-318",
                    "flight_date": "12 OCT",
                    "dep_time": "05:45 AM",
                    "arr_time": "08:30 AM"
                }
            ]
        },

        # 8. Gulf Air - ISB ➔ BAH ➔ JED (Via Round Trip)
        {
            "airline": saudia,
            "airline_name_custom": "Gulf Air",
            "departure_city": "Islamabad (ISB)",
            "destination_city": "Jeddah (JED)",
            "departure_time": "06:00 AM",
            "arrival_time": "11:45 AM",
            "return_departure_time": "02:30 PM",
            "return_arrival_time": "11:15 PM",
            "trip_type": "return",
            "route_type": "via",
            "via_city": "Bahrain (BAH)",
            "has_meal": True,
            "total_seats": 65,
            "available_seats": 48,
            "min_group_size": 12,
            "discount_type": "flat",
            "discount_value": Decimal("19000.00"),
            "baggage_weight_kg": 30,
            "return_baggage_weight_kg": 30,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Islamabad (ISB)",
                    "to_city": "Bahrain (BAH)",
                    "flight_no": "GF-771",
                    "flight_date": "18 OCT",
                    "dep_time": "06:00 AM",
                    "arr_time": "08:15 AM"
                },
                {
                    "from_city": "Bahrain (BAH)",
                    "to_city": "Jeddah (JED)",
                    "flight_no": "GF-165",
                    "flight_date": "18 OCT",
                    "dep_time": "09:30 AM",
                    "arr_time": "11:45 AM"
                },
                {
                    "from_city": "Jeddah (JED)",
                    "to_city": "Bahrain (BAH)",
                    "flight_no": "GF-166",
                    "flight_date": "02 NOV",
                    "dep_time": "02:30 PM",
                    "arr_time": "04:45 PM"
                },
                {
                    "from_city": "Bahrain (BAH)",
                    "to_city": "Islamabad (ISB)",
                    "flight_no": "GF-772",
                    "flight_date": "02 NOV",
                    "dep_time": "06:15 PM",
                    "arr_time": "11:15 PM"
                }
            ]
        },

        # 9. SalamAir - LHE ➔ MCT ➔ MED (Via One Way)
        {
            "airline": saudia,
            "airline_name_custom": "SalamAir",
            "departure_city": "Lahore (LHE)",
            "destination_city": "Madinah (MED)",
            "departure_time": "01:30 AM",
            "arrival_time": "07:15 AM",
            "trip_type": "oneway",
            "route_type": "via",
            "via_city": "Muscat (MCT)",
            "has_meal": True,
            "total_seats": 50,
            "available_seats": 42,
            "min_group_size": 10,
            "discount_type": "flat",
            "discount_value": Decimal("9000.00"),
            "baggage_weight_kg": 30,
            "return_baggage_weight_kg": 0,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Lahore (LHE)",
                    "to_city": "Muscat (MCT)",
                    "flight_no": "OV-552",
                    "flight_date": "24 OCT",
                    "dep_time": "01:30 AM",
                    "arr_time": "03:45 AM"
                },
                {
                    "from_city": "Muscat (MCT)",
                    "to_city": "Madinah (MED)",
                    "flight_no": "OV-214",
                    "flight_date": "24 OCT",
                    "dep_time": "05:00 AM",
                    "arr_time": "07:15 AM"
                }
            ]
        },

        # 10. AirSial - KHI ➔ ISB (Domestic Direct One Way)
        {
            "airline": saudia,
            "airline_name_custom": "AirSial",
            "departure_city": "Karachi (KHI)",
            "destination_city": "Islamabad (ISB)",
            "departure_time": "07:00 PM",
            "arrival_time": "09:00 PM",
            "trip_type": "oneway",
            "route_type": "direct",
            "via_city": "",
            "has_meal": True,
            "total_seats": 40,
            "available_seats": 32,
            "min_group_size": 8,
            "discount_type": "flat",
            "discount_value": Decimal("5000.00"),
            "baggage_weight_kg": 20,
            "return_baggage_weight_kg": 0,
            "is_active": True,
            "sectors_data": [
                {
                    "from_city": "Karachi (KHI)",
                    "to_city": "Islamabad (ISB)",
                    "flight_no": "PF-121",
                    "flight_date": "30 OCT",
                    "dep_time": "07:00 PM",
                    "arr_time": "09:00 PM"
                }
            ]
        }
    ]

    count = 0
    for ticket in group_tickets_data:
        g = GroupFarePolicy.objects.create(**ticket)
        count += 1
        print(f"[{count}/10] Created Group Ticket #{g.id}: {g.airline_name_custom} ({g.departure_city} -> {g.destination_city}) - {g.trip_type.upper()}")

    print(f"\nSuccessfully created {count} group tickets in GroupFarePolicy!")

if __name__ == '__main__':
    seed_10_group_tickets()
