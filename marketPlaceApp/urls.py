from django.urls import path
from marketPlaceApp import views

urlpatterns = [
    path('', views.GeneralMarket.as_view(), name='generalMarket'),
]
