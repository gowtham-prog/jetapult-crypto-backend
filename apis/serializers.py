from rest_framework import serializers
from .models import Coin, HistoricalPrice, FavoriteCoin
from django.contrib.auth.models import User

class HistoricalPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalPrice
        fields = ["date", "price"]


class CoinSerializer(serializers.ModelSerializer):
    is_favorite = serializers.SerializerMethodField()

    def get_is_favorite(self, obj):
        return getattr(obj, "is_favorite", False)
    class Meta:
        model = Coin
        fields = [
            "id",
            "coingecko_id",
            "symbol",
            "name",
            "market_cap_rank",
            "last_price",
            "volume",
            "percent_change_24h",
            "updated_at",
            "is_favorite",
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


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        return user

class FavoriteCoinSerializer(serializers.ModelSerializer):
    coin_name = serializers.CharField(source="coin.name", read_only=True)
    coin_symbol = serializers.CharField(source="coin.symbol", read_only=True)

    class Meta:
        model = FavoriteCoin
        fields = ["id", "coin", "coin_name", "coin_symbol", "created_at"]
        read_only_fields = ["id", "created_at", "coin_name", "coin_symbol"]

    def validate_coin(self, value):
        """
        Ensure coin exists in DB before adding.
        """
        if not Coin.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Coin does not exist.")
        return value

    def perform_create(self, serializer):
        if FavoriteCoin.objects.filter(user=self.request.user, coin=serializer.validated_data["coin"]).exists():
            raise serializers.ValidationError("Coin is already in your favorites.")
        serializer.save(user=self.request.user)
