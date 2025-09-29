from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from django.db.models import Exists, OuterRef



from .models import Coin, HistoricalPrice,FavoriteCoin
from .serializers import CoinSerializer, CoinWithHistorySerializer, HistoricalPriceSerializer
from .qa import handle_query

# Create your views here.

class TopCoinsView(generics.ListAPIView):
    """
    GET /api/coins/top/?n=10
    Returns the top N coins ordered by market_cap_rank
    """
    serializer_class = CoinSerializer
    permission_classes = [ IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        n = self.request.query_params.get("n", 10)
        try:
            n = int(n)
        except ValueError:
            n = 10

        return (
            Coin.objects
            .order_by("market_cap_rank")
            .annotate(
                is_favorite=Exists(
                    FavoriteCoin.objects.filter(user=user, coin=OuterRef("pk"))
                )
            )[:n]
        )

class CoinHistoryView(APIView):
    """
    GET /api/coins/<coingecko_id>/history/?days=30
    Returns the historical prices for the given coin for the last X days
    """
    permission_classes = [ IsAuthenticated]

    def get(self, request, coingecko_id):
        coin = get_object_or_404(Coin, coingecko_id=coingecko_id)

        days = request.query_params.get("days", 30)
        try:
            days = int(days)
        except ValueError:
            days = 30

        start_date = date.today() - timedelta(days=days)
        history_qs = coin.history.filter(date__gte=start_date).order_by("date")

        serializer = HistoricalPriceSerializer(history_qs, many=True)
        return Response({
            "coin": CoinSerializer(coin).data,
            "history": serializer.data
        })


class QAView(APIView):
    """
    POST /api/qa/
    Accepts a natural language query and returns structured response
    """
    permission_classes = [ AllowAny]
    def post(self, request):
        query = request.data.get("query")
        if not query:
            return Response({"error": "Missing 'query' in request body"}, status=status.HTTP_400_BAD_REQUEST)

        result = handle_query(query)
        return Response(result)
