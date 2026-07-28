from django.db import models
from django.conf import settings

class VisaApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('submitted', 'Submitted to Embassy'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visa_applications')
    country = models.CharField(max_length=100)
    passport_number = models.CharField(max_length=50)
    visa_type = models.CharField(max_length=100, default='Tourist / Visitor Visa', blank=True, null=True)
    full_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.country} ({self.status})"

    def get_applicant_name(self):
        if self.full_name:
            return self.full_name
        return self.user.get_full_name() or self.user.username

    def get_applicant_email(self):
        if self.email:
            return self.email
        return self.user.email


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
    flag_icon = models.CharField(max_length=255, blank=True, null=True)
    banner_image = models.CharField(max_length=255, blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.country} - {self.title} (PKR {self.price})"

    def get_docs_list(self):
        if not self.required_documents:
            return ["Passport Copy", "Passport Size Photo", "CNIC Copy"]
        return [doc.strip() for doc in self.required_documents.split(',') if doc.strip()]


