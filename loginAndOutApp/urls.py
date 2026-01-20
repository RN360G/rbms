from django.urls import path
from loginAndOutApp import views

urlpatterns =[
    path('', views.LogIn.as_view(), name='login'),
    path('logout/<userID>', views.logout, name='logout'),
    path('createpass', views.CreatePassword.as_view(), name='createPassword')
]