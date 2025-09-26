from django.urls import path
from .views import TopCoinsView, CoinHistoryView, QAView, index, getUserAPIView


urlpatterns = [
    path('', index, name="index"),
    path('user', getUserAPIView.as_view(), name="User Apis"),
    path("coins/top/", TopCoinsView.as_view(), name="top-coins"),
    path("coins/<str:coingecko_id>/history/", CoinHistoryView.as_view(), name="coin-history"),
    path("qa/", QAView.as_view(), name="qa"),
]
