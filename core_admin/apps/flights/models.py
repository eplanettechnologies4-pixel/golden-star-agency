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


class FlightSector(models.Model):
    flight_ticket = models.ForeignKey(
        'flights.FlightTicketOffer',
        on_delete=models.CASCADE,
        related_name='sectors'
    )
    order = models.PositiveIntegerField()  # sequence: 1, 2, 3, 4
    airline_name = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=50, blank=True)
    departure_city = models.CharField(max_length=100)
    departure_airport_code = models.CharField(max_length=10, blank=True)
    arrival_city = models.CharField(max_length=100)
    arrival_airport_code = models.CharField(max_length=10, blank=True)
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Sector {self.order}: {self.departure_city} ({self.departure_airport_code}) -> {self.arrival_city} ({self.arrival_airport_code})"

    @property
    def dep_time_str(self):
        if self.departure_datetime:
            return self.departure_datetime.strftime('%I:%M %p')
        return '00:00'

    @property
    def arr_time_str(self):
        if self.arrival_datetime:
            return self.arrival_datetime.strftime('%I:%M %p')
        return '00:00'

    @property
    def dep_date_str(self):
        if self.departure_datetime:
            return self.departure_datetime.strftime('%d %b %Y')
        return ''


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
    ROUTE_TYPE_CHOICES = (
        ('one_way_direct', 'One Way (Direct Flight — 1 Sector)'),
        ('round_trip_direct', 'Round Trip (Direct Flight — 2 Sectors)'),
        ('multi_city_direct', 'Multi City (Direct Flight — 2 Sectors)'),
        ('one_way_via', 'One Way (Via Flight — 2 Sectors)'),
        ('round_trip_via', 'Round Trip (Via Flight — 4 Sectors)'),
        ('multi_city_via', 'Multi City (Via Flight — 4 Sectors)'),
    )
    TRIP_TYPE_CHOICES = (
        ('direct_oneway', 'Direct One-Way'),
        ('direct_roundtrip', 'Direct Round-Trip'),
        ('oneway_via', 'One-Way Via'),
        ('roundtrip_via', 'Round-Trip Via'),
        ('multicity', 'Multi-City'),
    )
    
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES, default='direct_oneway', blank=True, null=True)
    flight_route_type = models.CharField(max_length=35, default='round_trip_direct', choices=ROUTE_TYPE_CHOICES, blank=True, null=True)
    sectors_data = models.JSONField(default=list, blank=True, null=True)
    
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
    price_handcarry = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_20kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_23kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_25kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_30kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_35kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_40kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_46kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_baggage_fares = models.JSONField(default=dict, blank=True, null=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    baggage_checkin = models.CharField(max_length=50, default='30 kg')
    baggage_hand = models.CharField(max_length=50, default='7 kg')
    
    has_meal = models.BooleanField(default=True)
    meal_service = models.CharField(max_length=100, default='Meal Included')
    via_routes = models.CharField(max_length=255, blank=True, null=True, default='')
    
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

    def get_effective_sectors(self):
        """
        Returns structured list of sector objects or dicts for rendering itineraries.
        If FlightSector relational records exist, returns them ordered.
        Otherwise (for pre-existing/legacy tickets), synthesizes fallback sectors.
        """
        db_sectors = list(self.sectors.all().order_by('order'))
        if db_sectors:
            return db_sectors
        
        # Backward compatibility fallback synthesis for legacy tickets
        tt = self.trip_type or 'direct_oneway'
        dep_c = self.departure_city or 'Karachi (KHI)'
        dep_code = self.departure_airport_code or 'KHI'
        arr_c = self.destination_city or 'Jeddah (JED)'
        arr_code = self.destination_airport_code or 'JED'
        air_name = self.airline_name or 'Airline'
        fl_no = self.flight_number or 'FL-101'

        fallback_sectors = []
        if tt == 'direct_oneway':
            fallback_sectors.append({
                'order': 1,
                'airline_name': air_name,
                'flight_number': fl_no,
                'departure_city': dep_c,
                'departure_airport_code': dep_code,
                'arrival_city': arr_c,
                'arrival_airport_code': arr_code,
                'departure_time_str': self.departure_time_str,
                'arrival_time_str': self.arrival_time_str,
                'label': 'Direct Outbound'
            })
        elif tt == 'direct_roundtrip':
            fallback_sectors.append({
                'order': 1,
                'airline_name': air_name,
                'flight_number': fl_no,
                'departure_city': dep_c,
                'departure_airport_code': dep_code,
                'arrival_city': arr_c,
                'arrival_airport_code': arr_code,
                'departure_time_str': self.departure_time_str,
                'arrival_time_str': self.arrival_time_str,
                'label': 'Outbound'
            })
            fallback_sectors.append({
                'order': 2,
                'airline_name': air_name,
                'flight_number': fl_no,
                'departure_city': arr_c,
                'departure_airport_code': arr_code,
                'arrival_city': dep_c,
                'arrival_airport_code': dep_code,
                'departure_time_str': self.departure_time_str,
                'arrival_time_str': self.arrival_time_str,
                'label': 'Return'
            })
        elif tt == 'oneway_via':
            transit = (self.via_routes or 'Dubai (DXB)').split('→')[0].strip() or 'DXB'
            transit_code = transit[:3].upper()
            fallback_sectors.append({
                'order': 1,
                'airline_name': air_name,
                'flight_number': fl_no,
                'departure_city': dep_c,
                'departure_airport_code': dep_code,
                'arrival_city': transit,
                'arrival_airport_code': transit_code,
                'departure_time_str': self.departure_time_str,
                'arrival_time_str': self.arrival_time_str,
                'label': 'Leg 1'
            })
            fallback_sectors.append({
                'order': 2,
                'airline_name': air_name,
                'flight_number': fl_no,
                'departure_city': transit,
                'departure_airport_code': transit_code,
                'arrival_city': arr_c,
                'arrival_airport_code': arr_code,
                'departure_time_str': self.departure_time_str,
                'arrival_time_str': self.arrival_time_str,
                'label': 'Leg 2'
            })
        else: # roundtrip_via or multicity
            fallback_sectors.append({
                'order': 1,
                'airline_name': air_name,
                'flight_number': fl_no,
                'departure_city': dep_c,
                'departure_airport_code': dep_code,
                'arrival_city': arr_c,
                'arrival_airport_code': arr_code,
                'departure_time_str': self.departure_time_str,
                'arrival_time_str': self.arrival_time_str,
                'label': 'Sector 1'
            })
        return fallback_sectors

    def get_all_baggage_options(self):
        """
        Returns structured list of baggage fare tiers for dropdown select menu.
        """
        opts = []
        if self.price_handcarry and float(self.price_handcarry) > 0:
            opts.append({'key': 'handcarry', 'label': 'Hand Carry Only (7 KG)', 'price': float(self.price_handcarry)})
        
        base_20 = float(self.price_20kg) if (self.price_20kg and float(self.price_20kg) > 0) else float(self.price)
        opts.append({'key': '20kg', 'label': '20 KG Baggage Allowance', 'price': base_20})

        if self.price_23kg and float(self.price_23kg) > 0:
            opts.append({'key': '23kg', 'label': '23 KG Baggage Allowance', 'price': float(self.price_23kg)})
            
        if self.price_25kg and float(self.price_25kg) > 0:
            opts.append({'key': '25kg', 'label': '25 KG Baggage Allowance', 'price': float(self.price_25kg)})

        p_30 = float(self.price_30kg) if (self.price_30kg and float(self.price_30kg) > 0) else (base_20 + 15000.0)
        opts.append({'key': '30kg', 'label': '30 KG Baggage Allowance', 'price': p_30})

        if self.price_35kg and float(self.price_35kg) > 0:
            opts.append({'key': '35kg', 'label': '35 KG Baggage Allowance', 'price': float(self.price_35kg)})

        p_40 = float(self.price_40kg) if (self.price_40kg and float(self.price_40kg) > 0) else (base_20 + 30000.0)
        opts.append({'key': '40kg', 'label': '40 KG Baggage Allowance', 'price': p_40})

        if self.price_46kg and float(self.price_46kg) > 0:
            opts.append({'key': '46kg', 'label': '46 KG (2 PC x 23 KG)', 'price': float(self.price_46kg)})

        if isinstance(self.custom_baggage_fares, dict):
            for k, v in self.custom_baggage_fares.items():
                try:
                    val = float(v)
                    if val > 0:
                        opts.append({'key': str(k).lower(), 'label': f"{k} Baggage Allowance", 'price': val})
                except (ValueError, TypeError): pass

        return opts

    def get_sectors_info(self):
        """
        Returns sector list and count info based on flight_route_type and sectors_data.
        """
        secs = []
        if isinstance(self.sectors_data, list):
            secs = [str(s).strip().upper() for s in self.sectors_data if str(s).strip()]
        
        r_type = self.flight_route_type or 'round_trip_direct'
        
        # Fallback build if sectors_data is empty
        if not secs:
            dep = (self.departure_airport_code or self.departure_city or 'KHI')[:3].upper()
            dest = (self.destination_airport_code or self.destination_city or 'JED')[:3].upper()
            via = (self.via_routes or 'SHJ')[:3].upper()
            
            if r_type == 'one_way_direct':
                secs = [f"{dep}-{dest}"]
            elif r_type in ('round_trip_direct', 'multi_city_direct'):
                secs = [f"{dep}-{dest}", f"{dest}-{dep}"]
            elif r_type == 'one_way_via':
                secs = [f"{dep}-{via}", f"{via}-{dest}"]
            else: # round_trip_via, multi_city_via
                secs = [f"{dep}-{via}", f"{via}-{dest}", f"{dest}-{via}", f"{via}-{dep}"]

        count = len(secs)
        
        label_map = {
            'one_way_direct': f"{count} Sector (One Way Direct)",
            'round_trip_direct': f"{count} Sectors (Round Trip Direct)",
            'multi_city_direct': f"{count} Sectors (Multi City Direct)",
            'one_way_via': f"{count} Sectors (One Way Via)",
            'round_trip_via': f"{count} Sectors (Round Trip Via)",
            'multi_city_via': f"{count} Sectors (Multi City Via)",
        }
        
        label = label_map.get(r_type, f"{count} Sectors")

        return {
            'sectors': secs,
            'count': count,
            'label': label,
            'route_type': r_type
        }

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



