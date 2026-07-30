from django.db import migrations

def fix_superuser_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    # Update all accounts with is_superuser=True or is_staff=True that have default role='customer'
    superusers = User.objects.filter(is_superuser=True)
    for u in superusers:
        u.role = 'super_admin'
        u.is_email_verified = True
        u.save(update_fields=['role', 'is_email_verified'])
        
    staff_users = User.objects.filter(is_staff=True, role='customer')
    for u in staff_users:
        u.role = 'super_admin'
        u.is_email_verified = True
        u.save(update_fields=['role', 'is_email_verified'])

def reverse_fix(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_companydepartmentcontact'),
    ]

    operations = [
        migrations.RunPython(fix_superuser_roles, reverse_fix),
    ]
