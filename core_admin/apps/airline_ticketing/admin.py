from django.contrib import admin
from .models import Airline, AirlineFlightInventory, BaggageFareTier, GroupFarePolicy, AgentPackage, AgentTicketOrder, OrderPassenger


class BaggageFareTierInline(admin.TabularInline):
    model = BaggageFareTier
    extra = 1


class OrderPassengerInline(admin.TabularInline):
    model = OrderPassenger
    extra = 0


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'iata_code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'iata_code')


@admin.register(AirlineFlightInventory)
class AirlineFlightInventoryAdmin(admin.ModelAdmin):
    list_display = ('airline', 'departure_city', 'destination_city',
                    'departure_time', 'total_seats', 'booked_seats', 'is_active')
    list_filter = ('airline', 'is_active')
    search_fields = ('departure_city', 'destination_city')
    inlines = [BaggageFareTierInline]


@admin.register(BaggageFareTier)
class BaggageFareTierAdmin(admin.ModelAdmin):
    list_display = ('flight_inventory', 'weight_kg', 'fare')


@admin.register(GroupFarePolicy)
class GroupFarePolicyAdmin(admin.ModelAdmin):
    list_display = ('flight_inventory', 'min_group_size', 'discount_type', 'discount_value', 'baggage_weight_kg', 'is_active', 'created_at')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('flight_inventory__departure_city', 'flight_inventory__destination_city', 'flight_inventory__airline__name')


@admin.register(AgentPackage)
class AgentPackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'package_type', 'agent_price', 'suggested_resale_price', 'commission_amount', 'total_seats', 'booked_seats', 'is_active', 'created_at')
    list_filter = ('package_type', 'is_active')
    search_fields = ('title', 'description', 'makkah_hotel_name', 'madinah_hotel_name')


@admin.register(AgentTicketOrder)
class AgentTicketOrderAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'agent', 'order_type', 'total_fare', 'status', 'hold_expires_at', 'created_at')
    list_filter = ('order_type', 'status', 'created_at')
    search_fields = ('reference_number', 'agent__username', 'agent__email', 'traveler_contact_email', 'agent_contact_email')
    inlines = [OrderPassengerInline]


@admin.register(OrderPassenger)
class OrderPassengerAdmin(admin.ModelAdmin):
    list_display = ('order', 'first_name', 'last_name', 'passenger_type', 'nationality', 'passport_number')
    list_filter = ('passenger_type', 'nationality')
    search_fields = ('first_name', 'last_name', 'passport_number', 'order__reference_number')



