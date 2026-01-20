from django.urls import path
from warehouseApp import views

urlpatterns = [
    path('', views.warehouse, name='warehouse'),
    
]