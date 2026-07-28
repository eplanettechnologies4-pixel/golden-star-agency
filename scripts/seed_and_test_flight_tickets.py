import sys
import os

# Add core_admin folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.flights.models import FlightTicketOffer

print("--- Seeding Flight Ticket Offers ---")

sample_tickets = [
    {
        "airline_name": "PIA",
        "airline_code": "PK",
        "flight_number": "PK-731",
        "departure_city": "Karachi (KHI)",
        "departure_airport_code": "KHI",
        "destination_city": "Jeddah (JED)",
        "destination_airport_code": "JED",
        "departure_time_str": "03:30 AM",
        "arrival_time_str": "06:45 AM",
        "duration_str": "4h 15m",
        "flight_type": "direct",
        "ticket_class": "economy",
        "price": 145000.00,
        "original_price": 160000.00,
        "baggage_checkin": "30 kg",
        "baggage_hand": "7 kg",
        "is_refundable": True,
        "cancellation_fee": 15000.00,
        "total_seats": 50,
        "available_seats": 38,
        "is_popular": True,
        "description": "Direct non-stop flight on PIA Boeing 777. Free hot meal included."
    },
    {
        "airline_name": "Saudia",
        "airline_code": "SV",
        "flight_number": "SV-705",
        "departure_city": "Lahore (LHE)",
        "departure_airport_code": "LHE",
        "destination_city": "Madinah (MED)",
        "destination_airport_code": "MED",
        "departure_time_str": "11:15 PM",
        "arrival_time_str": "02:30 AM",
        "duration_str": "4h 15m",
        "flight_type": "direct",
        "ticket_class": "economy",
        "price": 165000.00,
        "original_price": 180000.00,
        "baggage_checkin": "2x 23 kg",
        "baggage_hand": "7 kg",
        "is_refundable": True,
        "cancellation_fee": 12000.00,
        "total_seats": 40,
        "available_seats": 25,
        "is_popular": True,
        "description": "Saudia 5-star direct service with Zamzam bottle allowance."
    },
    {
        "airline_name": "FlyDubai",
        "airline_code": "FZ",
        "flight_number": "FZ-334",
        "departure_city": "Islamabad (ISB)",
        "departure_airport_code": "ISB",
        "destination_city": "Dubai (DXB)",
        "destination_airport_code": "DXB",
        "departure_time_str": "07:00 AM",
        "arrival_time_str": "09:30 AM",
        "duration_str": "3h 30m",
        "flight_type": "direct",
        "ticket_class": "economy",
        "price": 95000.00,
        "original_price": 110000.00,
        "baggage_checkin": "30 kg",
        "baggage_hand": "7 kg",
        "is_refundable": True,
        "cancellation_fee": 10000.00,
        "total_seats": 60,
        "available_seats": 42,
        "is_popular": True,
        "description": "Express flight connecting Islamabad to Dubai Terminal 2."
    },
    {
        "airline_name": "SalamAir",
        "airline_code": "OV",
        "flight_number": "OV-502",
        "departure_city": "Multan (MUX)",
        "departure_airport_code": "MUX",
        "destination_city": "Muscat (MCT)",
        "destination_airport_code": "MCT",
        "departure_time_str": "01:20 PM",
        "arrival_time_str": "03:10 PM",
        "duration_str": "2h 50m",
        "flight_type": "direct",
        "ticket_class": "economy",
        "price": 78000.00,
        "original_price": 88000.00,
        "baggage_checkin": "20 kg",
        "baggage_hand": "7 kg",
        "is_refundable": True,
        "cancellation_fee": 8000.00,
        "total_seats": 45,
        "available_seats": 30,
        "is_popular": False,
        "description": "Budget non-stop flight to Muscat with transit options to Jeddah."
    },
    {
        "airline_name": "Air Arabia",
        "airline_code": "G9",
        "flight_number": "G9-541",
        "departure_city": "Peshawar (PEW)",
        "departure_airport_code": "PEW",
        "destination_city": "Sharjah (SHJ)",
        "destination_airport_code": "SHJ",
        "departure_time_str": "09:45 PM",
        "arrival_time_str": "12:15 AM",
        "duration_str": "3h 30m",
        "flight_type": "direct",
        "ticket_class": "economy",
        "price": 88000.00,
        "original_price": 98000.00,
        "baggage_checkin": "30 kg",
        "baggage_hand": "10 kg",
        "is_refundable": True,
        "cancellation_fee": 9000.00,
        "total_seats": 50,
        "available_seats": 19,
        "is_popular": False,
        "description": "Direct connectivity from Peshawar to Sharjah hub."
    }
]

for item in sample_tickets:
    ft, created = FlightTicketOffer.objects.get_or_create(
        flight_number=item["flight_number"],
        defaults=item
    )
    if created:
        print(f" [+] Created Ticket Offer: {ft.airline_name} ({ft.flight_number}) PKR {ft.price:,.2f}")
    else:
        print(f" [=] Existing Ticket Offer: {ft.airline_name} ({ft.flight_number})")

total = FlightTicketOffer.objects.count()
print(f"\nTotal Flight Ticket Offers in DB: {total}")
print("Flight Ticket Inventory Seeding Completed Successfully!")
