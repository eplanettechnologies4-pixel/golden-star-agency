from django.db import models
from django.conf import settings

class AirlinePartner(models.Model):
    name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50, default='fa-solid fa-plane')
    description = models.CharField(max_length=150, default='Official Partner')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Flight(models.Model):
    airline_name = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=50)
    departure_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    image = models.ImageField(upload_to='flights/', blank=True, null=True)
    static_image_name = models.CharField(max_length=100, blank=True, null=True, default='flights_banner.png')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.airline_name} {self.flight_number}: {self.departure_city} -> {self.destination_city}"

class FlightTicket(models.Model):
    CLASS_CHOICES = (
        ('economy', 'Economy Class'),
        ('business', 'Business Class'),
        ('first', 'First Class'),
    )
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='tickets')
    ticket_class = models.CharField(max_length=20, choices=CLASS_CHOICES, default='economy')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    baggage_allowance = models.CharField(max_length=50, default='30 KG')
    refund_policy = models.CharField(max_length=100, default='Refundable with fee')
    seats_available = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.get_ticket_class_display()} - PKR {self.price} ({self.flight.flight_number})"

class FlightQuoteRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Quote'),
        ('quoted', 'Quoted'),
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flight_requests')
    departure_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    departure_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    price_quote = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.departure_city} to {self.destination_city} ({self.status})"


class FlightTicketOffer(models.Model):
    CLASS_CHOICES = (
        ('economy', 'Economy Class'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business Class'),
        ('first', 'First Class'),
    )
    FLIGHT_TYPE_CHOICES = (
        ('direct', 'Non-Stop (Direct)'),
        ('one_stop', '1 Stop'),
        ('two_stop', '2 Stops'),
    )
    
    airline_name = models.CharField(max_length=100) # e.g. PIA, Saudi Arabian Airlines (Saudia), FlyDubai, SalamAir, Air Arabia
    airline_code = models.CharField(max_length=10, blank=True, null=True) # PK, SV, FZ, OV, G9
    airline_logo = models.CharField(max_length=255, blank=True, null=True) # Logo URL or icon
    flight_number = models.CharField(max_length=50) # e.g. SV-705, PK-731, FZ-334
    
    departure_city = models.CharField(max_length=100) # e.g. Karachi (KHI), Lahore (LHE), Islamabad (ISB)
    departure_airport_code = models.CharField(max_length=10, default='KHI')
    destination_city = models.CharField(max_length=100) # e.g. Jeddah (JED), Madinah (MED), Dubai (DXB), Muscat (MCT)
    destination_airport_code = models.CharField(max_length=10, default='JED')
    
    departure_time_str = models.CharField(max_length=50, default='03:30 AM')
    arrival_time_str = models.CharField(max_length=50, default='06:45 AM')
    duration_str = models.CharField(max_length=50, default='4h 15m')
    
    flight_type = models.CharField(max_length=20, choices=FLIGHT_TYPE_CHOICES, default='direct')
    ticket_class = models.CharField(max_length=30, choices=CLASS_CHOICES, default='economy')
    
    price = models.DecimalField(max_digits=10, decimal_places=2) # Base ticket price per seat in PKR
    price_20kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_30kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_40kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    baggage_checkin = models.CharField(max_length=50, default='30 kg')
    baggage_hand = models.CharField(max_length=50, default='7 kg')
    
    is_refundable = models.BooleanField(default=True)
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00)
    
    total_seats = models.IntegerField(default=50)
    available_seats = models.IntegerField(default=50)
    
    is_popular = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.airline_name} {self.flight_number}: {self.departure_city} -> {self.destination_city} (PKR {self.price})"

    @property
    def get_price_20kg(self):
        return self.price_20kg if self.price_20kg else self.price

    @property
    def get_price_30kg(self):
        if self.price_30kg:
            return self.price_30kg
        return self.price + 15000

    @property
    def get_price_40kg(self):
        if self.price_40kg:
            return self.price_40kg
        return self.price + 30000



