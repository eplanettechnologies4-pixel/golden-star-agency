import sys
import os

# Add core_admin to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.core.files.base import ContentFile
from apps.accounts.models import AgentLedger

User = get_user_model()

def create_agent():
    username = 'dummy_agent'
    email = 'agent@goldenstar.com'
    password = 'Password@123'
    
    # 1x1 transparent PNG bytes
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\x60\x00\x00\x00\x02\x00\x01\x48\xaf\xa4\x71\x00\x00\x00\x00IEND\xaeB`\x82'
    
    user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'role': 'agent'})
    
    user.set_password(password)
    user.email = email
    user.role = 'agent'
    user.approval_status = 'approved'
    user.is_email_verified = True
    user.is_active = True
    user.first_name = 'Tariq'
    user.last_name = 'Mahmood'
    user.company_name = 'Golden Star Express Travel Agency'
    user.address = 'Suite #302, Business Avenue, Main Boulevard, Gulberg III, Lahore, Pakistan'
    user.phone = '+92 300 9876543'
    user.about = 'Certified Platinum B2B Partner handling Umrah, Hajj, Flight Tickets & Visa services.'
    user.is_verified_partner = True
    user.rating = 4.9
    
    if not user.profile_photo:
        user.profile_photo.save('dummy_agent_profile.png', ContentFile(png_bytes), save=False)
    if not user.id_card_front:
        user.id_card_front.save('dummy_agent_cnic_front.png', ContentFile(png_bytes), save=False)
    if not user.id_card_back:
        user.id_card_back.save('dummy_agent_cnic_back.png', ContentFile(png_bytes), save=False)
        
    user.save()
    
    # Also ensure there's a starter wallet credit entry for testing wallet balance if empty
    if not user.ledger_entries.exists():
        AgentLedger.objects.create(
            agent=user,
            entry_type='credit',
            category='advance',
            amount=50000.00,
            description='Initial Opening Credit Balance for Testing',
            reference='INIT-CREDIT-001'
        )
        print("Created starter wallet balance: PKR 50,000")
        
    auth_user = authenticate(username=username, password=password)
    print(f"==================================================")
    print(f"Dummy Agent Account Ready!")
    print(f"Username: {username}")
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print(f"Role:     {user.role}")
    print(f"Status:   {user.approval_status}")
    print(f"Auth OK:  {auth_user is not None}")
    print(f"Wallet:   PKR {user.wallet_balance}")
    print(f"==================================================")

if __name__ == '__main__':
    create_agent()
