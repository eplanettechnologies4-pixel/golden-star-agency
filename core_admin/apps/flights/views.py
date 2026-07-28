from django.shortcuts import render, get_object_or_404
from .models import Flight, FlightTicket, AirlinePartner, FlightTicketOffer

def flight_list_view(request):
    flights = Flight.objects.filter(is_active=True).prefetch_related('tickets')
    partners = AirlinePartner.objects.filter(is_active=True)
    flight_tickets = FlightTicketOffer.objects.all().order_by('-is_popular', 'price')
    
    # Dynamic distinct dropdown choices
    distinct_airlines = list(FlightTicketOffer.objects.values_list('airline_name', flat=True).distinct())
    departure_cities = list(FlightTicketOffer.objects.values_list('departure_city', flat=True).distinct())
    destination_cities = list(FlightTicketOffer.objects.values_list('destination_city', flat=True).distinct())
    
    return render(request, 'flights/flights_list.html', {
        'flights': flights,
        'partners': partners,
        'flight_tickets': flight_tickets,
        'distinct_airlines': sorted(distinct_airlines),
        'departure_cities': sorted(departure_cities),
        'destination_cities': sorted(destination_cities),
    })

def flight_detail_view(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    tickets = flight.tickets.all()
    return render(request, 'flights/flight_detail.html', {
        'flight': flight,
        'tickets': tickets
    })
