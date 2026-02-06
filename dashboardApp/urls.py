from django.urls import path
from dashboardApp import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('buycode', views.BuyCode.as_view(), name='buyCode'),
    path('salesselectprinter', views.selectPrinter, name='salesSelectPrinter'),
]