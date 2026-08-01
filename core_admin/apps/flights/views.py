from django.shortcuts import render, get_object_or_404
from .models import Flight, FlightTicket, AirlinePartner, FlightTicketOffer
from apps.airline_ticketing.models import Sector, Airline

def flight_list_view(request):
    flights = Flight.objects.filter(is_active=True).prefetch_related('tickets')
    partners = AirlinePartner.objects.filter(is_active=True)
    flight_tickets = list(FlightTicketOffer.objects.all().order_by('-is_popular', 'price'))
    master_airlines = list(Airline.objects.filter(is_active=True))
    
    # Map logo to tickets if ticket.airline_logo is missing
    airline_logo_map = {a.name.lower(): a.logo.url for a in master_airlines if a.logo}
    for ticket in flight_tickets:
        if not ticket.airline_logo and ticket.airline_name.lower() in airline_logo_map:
            ticket.airline_logo = airline_logo_map[ticket.airline_name.lower()]

    # Dynamic distinct dropdown choices
    ticket_airlines = list(FlightTicketOffer.objects.values_list('airline_name', flat=True).distinct())
    master_airline_names = [a.name for a in master_airlines]
    all_airlines = sorted(list(set(filter(None, ticket_airlines + master_airline_names))))

    departure_cities = list(FlightTicketOffer.objects.values_list('departure_city', flat=True).distinct())
    destination_cities = list(FlightTicketOffer.objects.values_list('destination_city', flat=True).distinct())
    
    # Active sectors from sector master table
    sectors = list(Sector.objects.filter(is_active=True))
    
    # Also form sector routes from flight tickets
    sector_routes = set()
    for s in sectors:
        sector_routes.add(f"{s.origin_city.upper()} → {s.destination_city.upper()}")
    for ticket in flight_tickets:
        dep = ticket.departure_city.split('(')[0].strip().upper()
        dest = ticket.destination_city.split('(')[0].strip().upper()
        sector_routes.add(f"{dep} → {dest}")

    return render(request, 'flights/flights_list.html', {
        'flights': flights,
        'partners': partners,
        'flight_tickets': flight_tickets,
        'master_airlines': master_airlines,
        'distinct_airlines': all_airlines,
        'departure_cities': sorted([c for c in departure_cities if c]),
        'destination_cities': sorted([c for c in destination_cities if c]),
        'sector_routes': sorted(list(sector_routes)),
        'sectors': sectors,
    })

def flight_detail_view(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    tickets = flight.tickets.all()
    return render(request, 'flights/flight_detail.html', {
        'flight': flight,
        'tickets': tickets
    })
