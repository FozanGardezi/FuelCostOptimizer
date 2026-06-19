# Generated manually because Django is not installed in the execution environment.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='TruckstopFuelPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opis_truckstop_id', models.PositiveIntegerField(db_index=True)),
                ('truckstop_name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=120)),
                ('state', models.CharField(db_index=True, max_length=2)),
                ('rack_id', models.PositiveIntegerField(blank=True, null=True)),
                ('retail_price', models.DecimalField(decimal_places=8, max_digits=10)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
            ],
            options={
                'ordering': ['state', 'city', 'truckstop_name'],
                'indexes': [models.Index(fields=['latitude', 'longitude'], name='optimizer_t_latitud_1c1894_idx'), models.Index(fields=['retail_price'], name='optimizer_t_retail__dfd183_idx')],
                'constraints': [models.UniqueConstraint(fields=('opis_truckstop_id', 'truckstop_name', 'address', 'city', 'state', 'rack_id'), name='unique_truckstop_fuel_price_location')],
            },
        ),
    ]
