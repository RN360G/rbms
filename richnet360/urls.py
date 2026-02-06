from django.urls import path
from richnet360 import views
from loginAndOutApp import views as loginViews

urlpatterns = [
    path('',loginViews.RichNetLogin.as_view(), name='richnetLogin'),
    path('richnetdasshboard', views.Richnet360.as_view(), name='richnetDashboard'),
    path('logoutrn360admin', loginViews.logoutRN360Admin, name='logoutRN360Admin'),
]

