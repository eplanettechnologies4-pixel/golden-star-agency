from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flights', '0006_flightticketoffer_has_meal_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='flightticketoffer',
            name='flight_route_type',
            field=models.CharField(blank=True, choices=[('one_way_direct', 'One Way (Direct Flight — 1 Sector)'), ('round_trip_direct', 'Round Trip (Direct Flight — 2 Sectors)'), ('multi_city_direct', 'Multi City (Direct Flight — 2 Sectors)'), ('one_way_via', 'One Way (Via Flight — 2 Sectors)'), ('round_trip_via', 'Round Trip (Via Flight — 4 Sectors)'), ('multi_city_via', 'Multi City (Via Flight — 4 Sectors)')], default='round_trip_direct', max_length=35, null=True),
        ),
        migrations.AddField(
            model_name='flightticketoffer',
            name='sectors_data',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]
