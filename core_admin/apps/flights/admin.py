from django.contrib import admin
from .models import Flight, FlightTicket, FlightQuoteRequest, AirlinePartner

@admin.register(AirlinePartner)
class AirlinePartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_class', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

class FlightTicketInline(admin.TabularInline):
    model = FlightTicket
    extra = 1

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('airline_name', 'flight_number', 'departure_city', 'destination_city', 'departure_time', 'arrival_time', 'is_active')
    list_filter = ('airline_name', 'is_active', 'departure_city', 'destination_city')
    search_fields = ('airline_name', 'flight_number', 'departure_city', 'destination_city')
    inlines = [FlightTicketInline]

@admin.register(FlightTicket)
class FlightTicketAdmin(admin.ModelAdmin):
    list_display = ('flight', 'ticket_class', 'price', 'seats_available')
    list_filter = ('ticket_class', 'flight')

@admin.register(FlightQuoteRequest)
class FlightQuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'departure_city', 'destination_city', 'departure_date', 'status', 'price_quote')
    list_filter = ('status', 'departure_date')
