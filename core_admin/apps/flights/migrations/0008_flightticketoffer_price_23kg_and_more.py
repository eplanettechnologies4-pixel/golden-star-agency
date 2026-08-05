from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flights', '0007_flightticketoffer_flight_route_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='flightticketoffer',
            name='price_23kg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='flightticketoffer',
            name='price_25kg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='flightticketoffer',
            name='price_35kg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='flightticketoffer',
            name='price_46kg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='flightticketoffer',
            name='custom_baggage_fares',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
