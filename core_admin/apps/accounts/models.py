from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('agent', 'Agent'),
        ('customer', 'Customer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    is_verified_partner = models.BooleanField(default=False)
    
    # Customer Verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    # Agent Verification Info
    company_name = models.CharField(max_length=100, blank=True, null=True)
    id_card_front = models.ImageField(upload_to='id_cards/', blank=True, null=True)
    id_card_back = models.ImageField(upload_to='id_cards/', blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='covers/', blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    rating = models.FloatField(default=5.0)
    
    # System-Generated Digital ID Badge
    agent_id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    id_card_issued_at = models.DateTimeField(null=True, blank=True)
    
    APPROVAL_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def wallet_balance(self):
        if self.role != 'agent':
            return 0.00
        credits_sum = self.ledger_entries.filter(entry_type='credit').aggregate(models.Sum('amount'))['amount__sum'] or 0
        debits_sum = self.ledger_entries.filter(entry_type='debit').aggregate(models.Sum('amount'))['amount__sum'] or 0
        return float(credits_sum - debits_sum)


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} logged in from {self.ip_address} at {self.timestamp}"


class AgentReview(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    author_name = models.CharField(max_length=100)
    rating = models.IntegerField(default=5) # 1 to 5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for {self.agent.company_name or self.agent.username} by {self.author_name} ({self.rating} stars)"


class AgentLedger(models.Model):
    """Financial ledger entry for a partner agent (commissions, payments, adjustments)."""
    ENTRY_TYPE_CHOICES = (
        ('credit', 'Credit'),     # Money owed TO agent
        ('debit',  'Debit'),      # Money owed FROM agent / charged
    )
    CATEGORY_CHOICES = (
        ('commission',   'Commission Earned'),
        ('payment',      'Payment Received'),
        ('refund',       'Refund Issued'),
        ('adjustment',   'Manual Adjustment'),
        ('penalty',      'Penalty / Deduction'),
        ('advance',      'Advance Payment'),
        ('ticket_purchase', 'Ticket Purchase'),
        ('other',        'Other'),
    )

    agent           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ledger_entries', limit_choices_to={'role': 'agent'})
    entry_type      = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    category        = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='commission')
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    running_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description     = models.TextField(blank=True)
    reference       = models.CharField(max_length=100, blank=True, help_text='Booking ID, invoice number, etc.')
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_created')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.entry_type.upper()}] {self.agent.company_name or self.agent.username} — PKR {self.amount} ({self.category})"


class AdminCustomBill(models.Model):
    """Manual custom bills, vendor invoices, supplier receipts, and agency expense entries."""
    DEPARTMENT_CHOICES = (
        ('umrah', 'Umrah Package'),
        ('hajj', 'Hajj Package'),
        ('visa', 'Visa Department'),
        ('ticket', 'Flight Ticket'),
        ('general', 'General Agency Expense'),
    )
    BILL_TYPE_CHOICES = (
        ('income', 'Agency Income / Bill'),
        ('expense', 'Agency Expense / Supplier Cost'),
    )

    bill_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=250)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='general')
    bill_type = models.CharField(max_length=10, choices=BILL_TYPE_CHOICES, default='expense')
    vendor_client_name = models.CharField(max_length=200, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.bill_number}] {self.title} — PKR {self.amount}"


class CompanyBankAccount(models.Model):
    """Official company bank accounts managed by admin and displayed to B2B agents for payment transfers."""
    bank_name = models.CharField(max_length=150)
    account_title = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100)
    iban = models.CharField(max_length=100, blank=True, null=True)
    branch_code = models.CharField(max_length=50, blank=True, null=True)
    branch_name = models.CharField(max_length=150, blank=True, null=True)
    swift_code = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bank_name} - {self.account_title} ({self.account_number})"


class AgentFeedback(models.Model):
    """Feedback, reviews, support tickets, and feature requests submitted by partner agents."""
    CATEGORY_CHOICES = (
        ('general', 'General Feedback'),
        ('ticket', 'Ticket Booking Issue'),
        ('wallet', 'Wallet & Payment Inquiry'),
        ('package', 'Pilgrimage / Package Query'),
        ('bug', 'Portal Bug / Improvement'),
        ('other', 'Other Topic'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    agent        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks_submitted', limit_choices_to={'role': 'agent'})
    category     = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    subject      = models.CharField(max_length=250)
    rating       = models.IntegerField(default=5)  # 1 to 5 stars
    message      = models.TextField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_reply  = models.TextField(blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.subject} — {self.agent.company_name or self.agent.username} ({self.rating} Stars)"


class CompanyDepartmentContact(models.Model):
    department_name = models.CharField(max_length=150)
    contact_person_name = models.CharField(max_length=150, blank=True, null=True)
    designation = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=50)
    whatsapp_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Company Department Contact'
        verbose_name_plural = 'Company Department Contacts'

    def __str__(self):
        return f"{self.department_name} - {self.contact_person_name or 'N/A'}"


