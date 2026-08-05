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
    is_round_trip = models.BooleanField(default=False)
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
    TRIP_TYPE_CHOICES = [('oneway', 'One Way'), ('return', 'Return / Round Trip'), ('multicity', 'Multi City')]
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

    trip_type = models.CharField(max_length=15, choices=TRIP_TYPE_CHOICES, default='return')
    route_type = models.CharField(max_length=10, choices=ROUTE_TYPE_CHOICES, default='direct')
    via_city = models.CharField(max_length=100, blank=True, null=True)
    has_meal = models.BooleanField(default=False)

    return_departure_time = models.CharField(max_length=50, blank=True, null=True)
    return_arrival_time = models.CharField(max_length=50, blank=True, null=True)
    return_route_type = models.CharField(max_length=10, choices=ROUTE_TYPE_CHOICES, blank=True, null=True)
    return_via_city = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    sectors_data = models.JSONField(
        default=list, blank=True,
        help_text='Per-leg details: [{"route":"LYP-SHJ","flight_no":"SV-734","dep_time":"03:30 AM","arr_time":"07:15 AM"}, ...]'
    )
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
    Group-specific pricing and ticket entries. Supports both standalone Group Flight Tickets
    and policies linked to an existing AirlineFlightInventory entry.
    """
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage (%)'),
        ('flat', 'Flat Amount (PKR)'),
    )

    flight_inventory = models.ForeignKey(
        AirlineFlightInventory,
        on_delete=models.CASCADE,
        related_name='group_policies',
        null=True,
        blank=True
    )
    airline = models.ForeignKey(
        Airline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='standalone_group_policies'
    )
    airline_name_custom = models.CharField(max_length=100, null=True, blank=True)
    departure_city = models.CharField(max_length=100, null=True, blank=True)
    destination_city = models.CharField(max_length=100, null=True, blank=True)
    departure_time = models.CharField(max_length=100, null=True, blank=True)
    arrival_time = models.CharField(max_length=100, null=True, blank=True)
    return_departure_time = models.CharField(max_length=100, null=True, blank=True)
    return_arrival_time = models.CharField(max_length=100, null=True, blank=True)
    trip_type = models.CharField(max_length=20, default='oneway') # oneway, return
    route_type = models.CharField(max_length=20, default='direct') # direct, via
    via_city = models.CharField(max_length=100, null=True, blank=True)
    has_meal = models.BooleanField(default=True)
    total_seats = models.PositiveIntegerField(default=50)
    available_seats = models.PositiveIntegerField(default=50)
    min_group_size = models.PositiveIntegerField(default=10, help_text='Minimum seats to qualify for group fare (e.g. 10)')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Discount percentage (0-100) or flat amount in PKR')
    baggage_weight_kg = models.PositiveIntegerField(default=30, help_text='Outbound Baggage allowance in KG')
    return_baggage_weight_kg = models.PositiveIntegerField(default=30, help_text='Return Baggage allowance in KG')
    base_fare = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    group_fare_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text='Override calculated net group fare directly')
    route_sectors = models.JSONField(default=list, blank=True, null=True, help_text='Structured leg/sector details: flight_no, dep/arr city, date, time')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Group Fare Policy'
        verbose_name_plural = 'Group Fare Policies'

    def __str__(self):
        air = self.airline.name if self.airline else (self.airline_name_custom or (self.flight_inventory.airline.name if self.flight_inventory else 'Group Ticket'))
        dep = self.departure_city or (self.flight_inventory.departure_city if self.flight_inventory else '')
        dest = self.destination_city or (self.flight_inventory.destination_city if self.flight_inventory else '')
        return f"Group Ticket: {air} ({dep} ➔ {dest}) — Min {self.min_group_size} seats"


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
    makkah_nights = models.PositiveIntegerField(default=7, help_text='Number of nights in Makkah')
    madinah_hotel_name = models.CharField(max_length=200, blank=True)
    madinah_hotel_distance = models.CharField(max_length=100, blank=True)
    madinah_nights = models.PositiveIntegerField(default=7, help_text='Number of nights in Madinah')

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
    cover_photo = models.ImageField(upload_to='umrah_packages/covers/', null=True, blank=True)

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

    @property
    def cover_photo_url(self):
        if self.cover_photo and hasattr(self.cover_photo, 'url'):
            return self.cover_photo.url
        if isinstance(self.images, list) and len(self.images) > 0 and self.images[0]:
            return self.images[0]
        if self.package_type == 'hajj':
            return "/static/images/hajj_card.png"
        return "/static/images/umrah_card.png"


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
        ('ticketed', 'Ticketed'),
        ('confirmed', 'Confirmed'),
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
    group_policy = models.ForeignKey(
        GroupFarePolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    agent_hajj_package = models.ForeignKey(
        'AgentHajjPackage',
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
    original_fare = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    admin_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
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
    CATEGORY_CHOICES = [
        ('economy', 'Economy Class'),
        ('economy_plus', 'Economy Plus'),
        ('1star', '1 Star Hotel'),
        ('2star', '2 Star Hotel'),
        ('3star', '3 Star Hotel'),
        ('4star', '4 Star Hotel'),
        ('5star', '5 Star Hotel'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='economy', blank=True)
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


class AgentHajjPackage(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    company_logo = models.ImageField(upload_to='agent_hajj/logos/', null=True, blank=True)
    duration_days = models.PositiveIntegerField()

    price_quad = models.DecimalField(max_digits=10, decimal_places=2)
    price_triple = models.DecimalField(max_digits=10, decimal_places=2)
    price_double = models.DecimalField(max_digits=10, decimal_places=2)
    price_sharing = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    hajj_operator_name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100)
    saudi_registration_number = models.CharField(max_length=100)

    # Travel Dates
    departure_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)

    # Meal Plan
    includes_meal = models.BooleanField(default=True)
    meal_detail = models.CharField(max_length=150, default='Full Board Buffet', blank=True, null=True)

    # Airline & Flight Info
    airline_name = models.CharField(max_length=150, default='Saudi Airlines', blank=True, null=True)
    airline_logo = models.ImageField(upload_to='agent_hajj/airlines/', null=True, blank=True)
    flight_name = models.CharField(max_length=150, blank=True, null=True)
    flight_route = models.CharField(max_length=255, default='KHI - JED - MED - KHI', blank=True, null=True)

    # Manual Hotel Summary (Makkah & Madinah)
    makkah_hotel_name = models.CharField(max_length=200, blank=True, default='')
    makkah_hotel_distance = models.CharField(max_length=100, blank=True, default='')
    madinah_hotel_name = models.CharField(max_length=200, blank=True, default='')
    madinah_hotel_distance = models.CharField(max_length=100, blank=True, default='')

    total_seats = models.PositiveIntegerField()
    available_seats = models.PositiveIntegerField()

    images = models.JSONField(default=list, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent Hajj Package'
        verbose_name_plural = 'Agent Hajj Packages'

    def __str__(self):
        return self.title

    @property
    def logo_url(self):
        if self.company_logo and hasattr(self.company_logo, 'url'):
            return self.company_logo.url
        return "/static/images/hajj_card.png"

    @property
    def airline_logo_url(self):
        if self.airline_logo and hasattr(self.airline_logo, 'url'):
            return self.airline_logo.url
        return None

    @property
    def starting_price(self):
        prices = [self.price_quad, self.price_triple, self.price_double]
        if self.price_sharing is not None:
            prices.append(self.price_sharing)
        valid_prices = [p for p in prices if p is not None]
        return min(valid_prices) if valid_prices else 0


class AgentHajjAccommodation(models.Model):
    CITY_CHOICES = [('makkah', 'Makkah'), ('madinah', 'Madinah')]

    agent_hajj_package = models.ForeignKey(AgentHajjPackage, on_delete=models.CASCADE, related_name='accommodations')
    city = models.CharField(max_length=20, choices=CITY_CHOICES)
    hotel = models.ForeignKey('airline_ticketing.Hotel', on_delete=models.SET_NULL, null=True, blank=True, related_name='agent_hajj_stays')
    manual_hotel_name = models.CharField(max_length=200, blank=True, default='')
    manual_hotel_distance = models.CharField(max_length=100, blank=True, default='')
    nights = models.PositiveIntegerField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Agent Hajj Accommodation'
        verbose_name_plural = 'Agent Hajj Accommodations'

    def __str__(self):
        h_name = self.hotel.name if self.hotel else (self.manual_hotel_name or 'Hotel')
        return f"{self.agent_hajj_package.title} - {self.get_city_display()}: {h_name} ({self.nights} nights)"


