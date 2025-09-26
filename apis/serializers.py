from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Coin, HistoricalPrice

User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
    

class HistoricalPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalPrice
        fields = ["date", "price"]


class CoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coin
        fields = [
            "coingecko_id",
            "symbol",
            "name",
            "market_cap_rank",
            "last_price",
            "volume",
            "percent_change_24h",
            "updated_at",
        ]


class CoinWithHistorySerializer(serializers.ModelSerializer):
    history = HistoricalPriceSerializer(many=True, read_only=True)

    class Meta:
        model = Coin
        fields = [
            "coingecko_id",
            "symbol",
            "name",
            "market_cap_rank",
            "last_price",
            "volume",
            "percent_change_24h",
            "updated_at",
            "history",
        ]
