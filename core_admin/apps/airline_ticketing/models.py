from django.db import models
from django.conf import settings


class Sector(models.Model):
    """
    Reusable Sector / Route definition (e.g. FAISALABAD-JEDDAH-FAISALABAD).
    Organizes multiple flight schedules and agent packages under a single route layer.
    """
    name = models.CharField(max_length=100)
    origin_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    is_round_trip = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectors'

    def __str__(self):
        return f"{self.name} ({self.origin_city} → {self.destination_city})"


class Airline(models.Model):
    """
    Master list of airlines managed by admin.
    Logo stored as uploaded image (uploaded_to='airlines/').
    """
    name = models.CharField(max_length=100)
    iata_code = models.CharField(max_length=10, blank=True, default='', help_text='IATA 2-letter airline code, e.g. PK, SV, EK')
    logo = models.ImageField(upload_to='airlines/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AirlineFlightInventory(models.Model):
    """
    A specific flight route operated by an Airline with seat inventory.
    Times stored as strings (e.g. '03:30 AM') — matches existing
    FlightTicketOffer.departure_time_str / arrival_time_str convention in apps.flights.
    """
    TRIP_TYPE_CHOICES = [('oneway', 'One Way'), ('return', 'Return')]
    ROUTE_TYPE_CHOICES = [('direct', 'Direct'), ('via', 'Via Connection')]

    sector = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        related_name='flights',
        null=True,
        blank=True
    )
    airline = models.ForeignKey(
        Airline,
        on_delete=models.CASCADE,
        related_name='flight_inventory'
    )
    departure_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    departure_time = models.CharField(max_length=50, default='00:00 AM')   # e.g. '03:30 AM'
    arrival_time = models.CharField(max_length=50, default='00:00 AM')     # e.g. '06:45 AM'
    total_seats = models.PositiveIntegerField(default=0)
    booked_seats = models.PositiveIntegerField(default=0)   # paid + active holds

    trip_type = models.CharField(max_length=10, choices=TRIP_TYPE_CHOICES, default='return')
    route_type = models.CharField(max_length=10, choices=ROUTE_TYPE_CHOICES, default='direct')
    via_city = models.CharField(max_length=100, blank=True, null=True)
    has_meal = models.BooleanField(default=False)

    return_departure_time = models.CharField(max_length=50, blank=True, null=True)
    return_arrival_time = models.CharField(max_length=50, blank=True, null=True)
    return_route_type = models.CharField(max_length=10, choices=ROUTE_TYPE_CHOICES, blank=True, null=True)
    return_via_city = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Flight Inventory'
        verbose_name_plural = 'Flight Inventories'

    def __str__(self):
        return (
            f"{self.airline.name}: {self.departure_city} → {self.destination_city} "
            f"({self.departure_time})"
        )

    @property
    def available_seats(self):
        return max(0, self.total_seats - self.booked_seats)


class BaggageFareTier(models.Model):
    """
    Per-kg baggage fare tier linked to a specific flight inventory entry.
    weight_kg examples: 7 (hand carry), 20, 30, 40.
    """
    flight_inventory = models.ForeignKey(
        AirlineFlightInventory,
        on_delete=models.CASCADE,
        related_name='baggage_tiers'
    )
    weight_kg = models.PositiveIntegerField(help_text='Baggage weight in KG, e.g. 7, 20, 30, 40')
    fare = models.DecimalField(max_digits=10, decimal_places=2, help_text='Fare in PKR')

    class Meta:
        ordering = ['weight_kg']

    def __str__(self):
        return (
            f"{self.flight_inventory} — {self.weight_kg}kg: PKR {self.fare}"
        )


class GroupFarePolicy(models.Model):
    """
    Group-specific pricing and discount rules linked to an AirlineFlightInventory entry.
    """
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage (%)'),
        ('flat', 'Flat Amount (PKR)'),
    )

    flight_inventory = models.ForeignKey(
        AirlineFlightInventory,
        on_delete=models.CASCADE,
        related_name='group_policies'
    )
    min_group_size = models.PositiveIntegerField(help_text='Minimum seats to qualify for group fare (e.g. 10)')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text='Discount percentage (0-100) or flat amount in PKR')
    baggage_weight_kg = models.PositiveIntegerField(default=20, help_text='Baggage allowance tier this policy applies to (e.g. 20, 30, 40)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Group Fare Policy'
        verbose_name_plural = 'Group Fare Policies'

    def __str__(self):
        val_str = f"{self.discount_value}%" if self.discount_type == 'percentage' else f"PKR {self.discount_value}"
        return f"{self.flight_inventory} — Min {self.min_group_size} seats ({val_str} off)"


class AgentPackage(models.Model):
    """
    B2B Travel Packages specifically for registered agents.
    Completely independent from the public B2C Package model.
    """
    PACKAGE_TYPE_CHOICES = (
        ('umrah', 'Umrah Package'),
        ('hajj', 'Hajj Package'),
    )

    sector = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        related_name='agent_packages',
        null=True,
        blank=True
    )
    package_type = models.CharField(max_length=10, choices=PACKAGE_TYPE_CHOICES, default='umrah')
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_days = models.IntegerField(default=15)
    
    agent_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Wholesale price charged to the agent (PKR)')
    suggested_resale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Suggested price agent charges client')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Estimated agent commission margin')

    # Per-passenger type pricing
    adult_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Wholesale adult price (PKR)')
    child_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Wholesale child price (PKR)')
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Wholesale infant price (PKR)')
    
    # Room Category Pricing (Sharing, Quad, Triple, Double)
    price_sharing = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Package price per person in Sharing Room (PKR)')
    price_quad = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Package price per person in Quad Room (PKR)')
    price_triple = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Package price per person in Triple Room (PKR)')
    price_double = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Package price per person in Double Room (PKR)')

    # Flight / Package travel dates
    departure_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)

    # Hotel Master linkages
    hotels = models.ManyToManyField('Hotel', related_name='agent_packages', blank=True)
    
    total_seats = models.PositiveIntegerField(default=30)
    booked_seats = models.PositiveIntegerField(default=0)

    makkah_hotel_name = models.CharField(max_length=200, blank=True)
    makkah_hotel_distance = models.CharField(max_length=100, blank=True)
    madinah_hotel_name = models.CharField(max_length=200, blank=True)
    madinah_hotel_distance = models.CharField(max_length=100, blank=True)

    airline = models.ForeignKey(
        Airline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_packages'
    )
    flight_name = models.CharField(max_length=150, default='Saudi Airlines', blank=True, null=True)
    flight_route_type = models.CharField(max_length=20, default='direct', choices=(('direct', 'Direct Flight'), ('via', 'Via Flight')), blank=True, null=True)
    flight_route = models.CharField(max_length=255, default='KHI - JED - MED - KHI', blank=True, null=True)
    
    includes_meal = models.BooleanField(default=True, help_text='Meal Included: Yes / No')
    meal_detail = models.CharField(max_length=100, default='Full Board', blank=True, null=True)
    transport_type = models.CharField(max_length=100, default='Sharing', blank=True, null=True)
    
    images = models.JSONField(default=list, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent Package'
        verbose_name_plural = 'Agent Packages'

    def __str__(self):
        return f"[{self.get_package_type_display()}] {self.title} (PKR {self.agent_price})"

    @property
    def available_seats(self):
        return max(0, self.total_seats - self.booked_seats)


class AgentTicketOrder(models.Model):
    ORDER_TYPE_CHOICES = (
        ('ticket', 'Ticket'),
        ('group', 'Group'),
        ('umrah', 'Umrah'),
        ('hajj', 'Hajj'),
    )
    STATUS_CHOICES = (
        ('hold', 'On Hold'),
        ('paid', 'Paid'),
        ('paid_pending', 'Payment Pending'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    SHARING_TYPE_CHOICES = (
        ('sharing', 'Sharing'),
        ('quad', 'Quad'),
        ('triple', 'Triple'),
        ('double', 'Double'),
    )

    reference_number = models.CharField(max_length=30, unique=True)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_orders'
    )
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='ticket')
    flight_inventory = models.ForeignKey(
        AirlineFlightInventory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    agent_package = models.ForeignKey(
        AgentPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    selected_hotel = models.ForeignKey(
        'Hotel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    selected_sharing_type = models.CharField(max_length=20, choices=SHARING_TYPE_CHOICES, null=True, blank=True)
    baggage_weight_kg = models.PositiveIntegerField(null=True, blank=True)
    traveler_contact_email = models.EmailField(blank=True, default='')
    agent_contact_email = models.EmailField()
    agent_phone_number = models.CharField(max_length=30, blank=True, null=True)
    total_fare = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='hold')
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    pnr = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent Ticket Order'
        verbose_name_plural = 'Agent Ticket Orders'

    def __str__(self):
        return f"{self.reference_number} ({self.get_order_type_display()}) — {self.agent.username}"


class OrderPassenger(models.Model):
    PASSENGER_TYPE_CHOICES = (
        ('adult', 'Adult'),
        ('child', 'Child'),
        ('infant', 'Infant'),
    )

    order = models.ForeignKey(
        AgentTicketOrder,
        on_delete=models.CASCADE,
        related_name='passengers'
    )
    passenger_type = models.CharField(max_length=10, choices=PASSENGER_TYPE_CHOICES, default='adult')
    title = models.CharField(max_length=10, blank=True, default='Mr')
    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True, default='Pakistan')
    passport_number = models.CharField(max_length=50, blank=True, default='')
    passport_image = models.FileField(upload_to='passports/', null=True, blank=True, help_text='Uploaded passport document image/copy')
    passport_issue_date = models.DateField(null=True, blank=True)
    passport_expiry_date = models.DateField(null=True, blank=True)
    allotted_ticket_number = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name} ({self.passenger_type})"


class Hotel(models.Model):
    CITY_CHOICES = [('makkah', 'Makkah'), ('madinah', 'Madinah')]

    name = models.CharField(max_length=200)
    city = models.CharField(max_length=20, choices=CITY_CHOICES)
    location = models.CharField(max_length=255, blank=True, default='', help_text='e.g. Ibrahim Khalil Road, Hijra Road')
    distance_from_haram = models.CharField(max_length=100, help_text='e.g. 500 meters or 350m from Haram')
    image = models.ImageField(upload_to='hotels/', null=True, blank=True)

    price_sharing = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_double = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_triple = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_quad = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Hotel'
        verbose_name_plural = 'Hotels'

    def __str__(self):
        return f"{self.name} ({self.get_city_display()})"


class SeatAdjustmentLog(models.Model):
    """
    Audit trail log for manual seat count adjustments performed by admins.
    NEVER referenced or read by any financial analytics queries or reports.
    """
    flight_inventory = models.ForeignKey(
        AirlineFlightInventory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='seat_adjustments'
    )
    agent_package = models.ForeignKey(
        AgentPackage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='seat_adjustments'
    )
    adjusted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    target_field = models.CharField(max_length=20, default='total_seats')  # 'total_seats' or 'booked_seats'
    old_value = models.IntegerField()
    new_value = models.IntegerField()
    reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Seat Adjustment Log'
        verbose_name_plural = 'Seat Adjustment Logs'

    def __str__(self):
        item = self.flight_inventory or self.agent_package or 'Unknown'
        return f"[Seat Log] {item} — {self.target_field}: {self.old_value} → {self.new_value}"


class BankAccount(models.Model):
    bank_name = models.CharField(max_length=150)
    account_title = models.CharField(max_length=150)
    account_number = models.CharField(max_length=100)
    bank_logo = models.ImageField(upload_to='banks/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['bank_name']
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"






