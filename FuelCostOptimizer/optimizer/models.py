from django.db import models


class TruckstopFuelPrice(models.Model):
    opis_truckstop_id = models.PositiveIntegerField(db_index=True)
    truckstop_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=2, db_index=True)
    rack_id = models.PositiveIntegerField(null=True, blank=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=8)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['state', 'city', 'truckstop_name']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['retail_price']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['opis_truckstop_id', 'truckstop_name', 'address', 'city', 'state', 'rack_id'],
                name='unique_truckstop_fuel_price_location',
            ),
        ]

    def __str__(self):
        return f'{self.truckstop_name} ({self.city}, {self.state}) - ${self.retail_price}'
