from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import AgentTicketOrder, AirlineFlightInventory, AgentPackage


@shared_task
def expire_stale_holds():
    """
    Run periodically via Celery Beat (every 5 minutes).
    Finds holds past their 2-hour window and releases the reserved seats.
    """
    expired_orders = AgentTicketOrder.objects.select_related('flight_inventory', 'agent_package').filter(
        status='hold',
        hold_expires_at__lt=timezone.now()
    )

    for order in expired_orders:
        with transaction.atomic():
            order.status = 'expired'
            order.save()

            requested_seats = order.passengers.count() or 1

            if order.flight_inventory:
                inv = AirlineFlightInventory.objects.select_for_update().get(id=order.flight_inventory_id)
                inv.booked_seats = max(0, inv.booked_seats - requested_seats)
                inv.save()

            if order.agent_package:
                pkg = AgentPackage.objects.select_for_update().get(id=order.agent_package_id)
                pkg.booked_seats = max(0, pkg.booked_seats - requested_seats)
                pkg.save()
