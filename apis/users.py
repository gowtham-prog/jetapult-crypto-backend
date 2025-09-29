from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import FavoriteCoin
from .serializers import FavoriteCoinSerializer, UserRegisterSerializer
from django.contrib.auth.models import User




class UserRegisterView(generics.CreateAPIView):
    """
    POST -> Register a new user
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

class FavoriteCoinListCreateView(generics.ListCreateAPIView):
    """
    GET  -> List user's favorite coins
    POST -> Add a coin to favorites
    """
    serializer_class = FavoriteCoinSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteCoin.objects.filter(user=self.request.user).select_related("coin")

    def perform_create(self, serializer):
        if FavoriteCoin.objects.filter(user=self.request.user, coin=serializer.validated_data["coin"]).exists():
            raise ValidationError("Coin is already in your favorites.")
        serializer.save(user=self.request.user)


class FavoriteCoinDeleteView(generics.DestroyAPIView):
    """
    DELETE -> Remove a coin from favorites
    """
    serializer_class = FavoriteCoinSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        coin_id = self.kwargs.get('coin_id')
        return FavoriteCoin.objects.get(user=self.request.user, coin_id=coin_id)
