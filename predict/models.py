from django.db import models


class PredResults(models.Model):

    client_name = models.CharField(max_length=30, default="")
    request_date = models.CharField(max_length=30, default="")
    start_date = models.CharField(max_length=30, default="")
    vehicle_size = models.IntegerField(default=0)
    pickup_postcode_1 = models.CharField(max_length=30, default="")
    pickup_city_1 = models.CharField(max_length=30, default="")
    dropoff_postcode_1 = models.CharField(max_length=30, default="")
    dropoff_city_1 = models.CharField(max_length=30, default="")
    number_pickups = models.IntegerField(default=0)
    number_shifts = models.IntegerField(default=0)
    number_trips = models.IntegerField(default=0)
    number_waits_returns = models.IntegerField(default=0)
    weekday = models.IntegerField(default=0)
    weekend = models.IntegerField(default=0)
    unsociable_hours = models.IntegerField(default=0)
    pred_price = models.FloatField(default=0)
    lower_price = models.FloatField(default=0)
    upper_price = models.FloatField(default=0)

    def __str__(self):
        return self.pred_price, self.lower_price, self.upper_price