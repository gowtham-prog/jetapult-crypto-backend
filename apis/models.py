from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Coin(models.Model):
    coingecko_id = models.CharField(max_length=128, unique=True)
    symbol = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    market_cap_rank = models.IntegerField(null=True)
    last_price = models.DecimalField(max_digits=30, decimal_places=10)
    volume = models.DecimalField(max_digits=30, decimal_places=2)
    percent_change_24h = models.FloatField(null=True)
    updated_at = models.DateTimeField(auto_now=True)

class HistoricalPrice(models.Model):
    coin = models.ForeignKey(Coin, related_name='history', on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(max_digits=30, decimal_places=10)

    class Meta:
        unique_together = ('coin', 'date')
        ordering = ['date']