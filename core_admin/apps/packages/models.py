from django.db import models

class Package(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50) # hajj, umrah, tour
    duration_days = models.IntegerField(default=15) # e.g. 15, 18, 28 days
    
    # Room sharing & child/infant pricing (4 Room Categories: Sharing, Quad, Triple, Double)
    price_sharing = models.DecimalField(max_digits=10, decimal_places=2, default=210000.00) # 5-6 bed room
    price_quad = models.DecimalField(max_digits=10, decimal_places=2, default=245000.00) # 4 bed room
    price_triple = models.DecimalField(max_digits=10, decimal_places=2, default=275000.00) # 3 bed room
    price_double = models.DecimalField(max_digits=10, decimal_places=2, default=320000.00) # 2 bed room
    price_child = models.DecimalField(max_digits=10, decimal_places=2, default=180000.00)
    price_infant = models.DecimalField(max_digits=10, decimal_places=2, default=65000.00) # Milk-feeding infant / child under 2 yrs (no bed)
    
    # Discount options
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Enhanced specification fields
    airline = models.CharField(max_length=100, default='Saudi Airlines', blank=True, null=True)
    airline_logo = models.CharField(max_length=255, blank=True, null=True)
    flight_routes = models.CharField(max_length=255, default='KHI - JED - MED - KHI', blank=True, null=True)
    flight_route_type = models.CharField(max_length=20, default='direct', choices=(('direct', 'Direct Flight'), ('via', 'Via Flight')), blank=True, null=True)
    
    includes_meal = models.BooleanField(default=True)
    meal_detail = models.CharField(max_length=100, default='Full Board', blank=True, null=True)
    transport_type = models.CharField(max_length=100, default='Sharing', blank=True, null=True)
    
    makkah_hotel_name = models.CharField(max_length=200, default='Anjum Hotel Makkah', blank=True, null=True)
    makkah_hotel_distance = models.CharField(max_length=100, default='350m from Haram', blank=True, null=True)
    makkah_hotel_images = models.JSONField(default=list, blank=True, null=True) # Makkah hotel photos
    
    madinah_hotel_name = models.CharField(max_length=200, default='Pullman Zamzam Madinah', blank=True, null=True)
    madinah_hotel_distance = models.CharField(max_length=100, default='150m from Prophet\'s Mosque', blank=True, null=True)
    madinah_hotel_images = models.JSONField(default=list, blank=True, null=True) # Madinah hotel photos
    
    luggage_weight = models.CharField(max_length=100, default='20 kg + 7 kg Hand Carry', blank=True, null=True)
    
    # Image gallery options (list of image URLs)
    images = models.JSONField(default=list, blank=True, null=True)
    
    # Optional Add-on options with extra prices (configured by admin)
    # Example: [{"id": "train", "name": "VIP Haramain High-Speed Train", "price": 25000}, ...]
    addons = models.JSONField(default=list, blank=True, null=True)
    
    # Seats tracking & announcement
    total_seats = models.IntegerField(default=30)
    available_seats = models.IntegerField(default=30)
    
    embedding = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_images_list(self):
        if isinstance(self.images, list) and len(self.images) > 0:
            return self.images
        return ["/static/images/umrah_card.png", "/static/images/hajj_card.png", "/static/images/turkey_card.png"]

    def get_all_hotel_and_package_images(self):
        imgs = []
        if isinstance(self.makkah_hotel_images, list):
            imgs.extend(self.makkah_hotel_images)
        if isinstance(self.madinah_hotel_images, list):
            imgs.extend(self.madinah_hotel_images)
        if isinstance(self.images, list):
            imgs.extend(self.images)
        if not imgs:
            imgs = self.get_images_list()
        # Deduplicate preserving order
        unique_imgs = []
        for img in imgs:
            if img and isinstance(img, str) and img.strip() and img not in unique_imgs:
                unique_imgs.append(img.strip())
        return unique_imgs if unique_imgs else self.get_images_list()

    def get_airline_info(self):
        name = self.airline or "Saudi Airlines"
        logo = self.airline_logo
        name_lower = name.lower()
        if logo:
            return {'name': name, 'logo_url': logo, 'icon_class': 'fa-plane'}
        elif 'pia' in name_lower or 'pakistan' in name_lower:
            return {'name': 'PIA (Pak International)', 'icon_class': 'fa-plane-departure', 'badge_color': 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'}
        elif 'saudi' in name_lower or 'saudia' in name_lower:
            return {'name': 'Saudi Airlines (Saudia)', 'icon_class': 'fa-plane-up', 'badge_color': 'bg-amber-500/10 text-amber-600 border-amber-500/20'}
        elif 'flydubai' in name_lower:
            return {'name': 'FlyDubai', 'icon_class': 'fa-plane', 'badge_color': 'bg-orange-500/10 text-orange-600 border-orange-500/20'}
        elif 'emirates' in name_lower:
            return {'name': 'Emirates', 'icon_class': 'fa-plane', 'badge_color': 'bg-red-500/10 text-red-600 border-red-500/20'}
        elif 'qatar' in name_lower:
            return {'name': 'Qatar Airways', 'icon_class': 'fa-plane', 'badge_color': 'bg-purple-500/10 text-purple-600 border-purple-500/20'}
        elif 'air arabia' in name_lower:
            return {'name': 'Air Arabia', 'icon_class': 'fa-plane', 'badge_color': 'bg-rose-500/10 text-rose-600 border-rose-500/20'}
        return {'name': name, 'icon_class': 'fa-plane', 'badge_color': 'bg-blue-500/10 text-blue-600 border-blue-500/20'}



class CustomPackageInquiry(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='custom_inquiries')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    package_type = models.CharField(max_length=10) # 'hajj' or 'umrah'
    days = models.IntegerField() # 7, 10, 21, 30
    makkah_distance = models.IntegerField() # range 0 to 2000
    madinah_distance = models.IntegerField() # range 0 to 2000
    airline = models.CharField(max_length=50) # 'PIA', 'Saudi Airlines', etc.
    additional_notes = models.TextField(blank=True, null=True)
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.package_type.upper()} ({self.days} Days)"


