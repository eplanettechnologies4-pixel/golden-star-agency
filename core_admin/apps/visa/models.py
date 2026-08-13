from django.db import models
from django.conf import settings

class VisaPackage(models.Model):
    ENTRY_CHOICES = (
        ('single', 'Single Entry'),
        ('multiple', 'Multiple Entry'),
    )
    country = models.CharField(max_length=100) # e.g. Saudi Arabia, UAE, Turkey, UK, Malaysia, Oman
    title = models.CharField(max_length=200) # e.g. Saudi Arabia 1-Year Tourist eVisa
    visa_type = models.CharField(max_length=100, default='Tourist / Visitor Visa')
    processing_time = models.CharField(max_length=100, default='3 to 5 Working Days')
    stay_validity = models.CharField(max_length=100, default='90 Days Stay')
    visa_validity = models.CharField(max_length=100, default='1 Year Validity')
    entry_type = models.CharField(max_length=50, choices=ENTRY_CHOICES, default='multiple')
    price = models.DecimalField(max_digits=10, decimal_places=2) # e.g. 45000.00
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    required_documents = models.TextField(default="Passport Copy (6 Months Validity), Passport Size Photo with White Background, CNIC Copy")
    description = models.TextField(blank=True, null=True)
    group_name = models.CharField(max_length=200, blank=True, null=True, default='')
    tower_hotel_details = models.CharField(max_length=255, blank=True, null=True, default='')
    flag_icon = models.CharField(max_length=255, blank=True, null=True)
    banner_image = models.CharField(max_length=255, blank=True, null=True)
    cover_image = models.ImageField(upload_to='visa_covers/', blank=True, null=True)
    flyer_document = models.FileField(upload_to='visa_flyers/', blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    is_multi_country = models.BooleanField(default=False)
    countries_included = models.CharField(max_length=255, blank=True, null=True, default='')
    tour_destinations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.country} - {self.title} (PKR {self.price})"

    def get_docs_list(self):
        if not self.required_documents:
            return ["Passport Copy", "Passport Size Photo", "CNIC Copy"]
        return [doc.strip() for doc in self.required_documents.split(',') if doc.strip()]

    @property
    def cover_url(self):
        if self.cover_image:
            return self.cover_image.url
        if self.banner_image:
            return self.banner_image
        country_lower = self.country.lower() if self.country else ''
        if 'saudi' in country_lower:
            return '/static/images/saudi_visa.png'
        elif 'turkey' in country_lower:
            return '/static/images/turkey_visa.png'
        elif 'malaysia' in country_lower:
            return '/static/images/malaysia_visa.png'
        elif 'dubai' in country_lower or 'uae' in country_lower or 'emirates' in country_lower:
            return '/static/images/dubai_visa.png'
        elif 'uk' in country_lower or 'britain' in country_lower or 'kingdom' in country_lower:
            return '/static/images/uk_visa.png'
        elif 'thailand' in country_lower:
            return '/static/images/thailand_visa.png'
        return '/static/images/visa_banner.png'


class VisaApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('submitted', 'Submitted to Embassy'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='visa_applications')
    visa_package = models.ForeignKey(VisaPackage, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    country = models.CharField(max_length=100)
    passport_number = models.CharField(max_length=50, blank=True, null=True, default='')
    visa_type = models.CharField(max_length=100, default='Tourist / Visitor Visa', blank=True, null=True)
    full_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    additional_notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = self.get_applicant_name()
        return f"{name} - {self.country} ({self.status})"

    def get_applicant_name(self):
        if self.full_name:
            return self.full_name
        if self.user:
            return self.user.get_full_name() or self.user.username
        return 'Guest Applicant'

    def get_applicant_email(self):
        if self.email:
            return self.email
        if self.user:
            return self.user.email
        return 'N/A'


