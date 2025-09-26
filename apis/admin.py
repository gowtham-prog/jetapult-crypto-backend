from django.contrib import admin
from .models import Coin, HistoricalPrice

# Register your models here.
admin.site.register(Coin)
admin.site.register(HistoricalPrice)