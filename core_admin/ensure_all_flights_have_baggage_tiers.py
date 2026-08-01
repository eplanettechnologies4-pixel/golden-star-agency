import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.airline_ticketing.models import AirlineFlightInventory, BaggageFareTier

print("=== CHECKING B2B FLIGHT INVENTORIES FOR BAGGAGE FARE TIERS ===")
routes = AirlineFlightInventory.objects.all()
updated_routes = 0

for fi in routes:
    tiers_count = fi.baggage_tiers.count()
    if tiers_count == 0:
        BaggageFareTier.objects.create(flight_inventory=fi, weight_kg=20, fare=50000.00)
        BaggageFareTier.objects.create(flight_inventory=fi, weight_kg=30, fare=55000.00)
        BaggageFareTier.objects.create(flight_inventory=fi, weight_kg=40, fare=60000.00)
        updated_routes += 1
        print(f"Created default baggage tiers (20KG, 30KG, 40KG) for Route #{fi.id}: {fi.departure_city} -> {fi.destination_city}")

print(f"Total Routes updated with baggage tiers: {updated_routes}")
