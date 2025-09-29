from django.urls import path
from .views import TopCoinsView, CoinHistoryView, QAView
from .users import FavoriteCoinListCreateView, FavoriteCoinDeleteView, UserRegisterView


urlpatterns = [

    path("coins/top/", TopCoinsView.as_view(), name="top-coins"),
    path("coins/<str:coingecko_id>/history/", CoinHistoryView.as_view(), name="coin-history"),
    path("qa/", QAView.as_view(), name="qa"),
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("favorites/", FavoriteCoinListCreateView.as_view(), name="favorite-coin-list-create"),
    path("favorites/<int:coin_id>/", FavoriteCoinDeleteView.as_view(), name="favorite-coin-delete"),

]
