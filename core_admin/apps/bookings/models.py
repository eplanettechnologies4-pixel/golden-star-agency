from django.db import models
from django.conf import settings
from apps.packages.models import Package

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    TYPE_CHOICES = (
        ('package', 'Package Booking'),
        ('custom', 'Custom Booking'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    booking_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='package')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pnr = models.CharField(max_length=50, blank=True, null=True, default='')
    full_name = models.CharField(max_length=200, blank=True, null=True, default='')
    email = models.EmailField(blank=True, null=True, default='')
    phone_number = models.CharField(max_length=50, blank=True, null=True, default='')
    
    # Room sharing & breakdown
    sharing_category = models.CharField(max_length=50, default='Quad', blank=True, null=True)
    adults_count = models.IntegerField(default=1)
    children_count = models.IntegerField(default=0)
    infants_count = models.IntegerField(default=0) # Milk-feeding small children (0-2 yrs)
    selected_addons = models.JSONField(default=list, blank=True, null=True) # Selected optional addons with prices
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_label = self.user.username if self.user else (self.full_name or self.email or 'Guest')
        return f"Booking #{self.id} - {user_label} ({self.status})"


