from django.urls import path
from loginAndOutApp import views

urlpatterns =[
    path('', views.LogIn.as_view(), name='login'),
    path('logout/<userID>', views.logout, name='logout'),
    path('createpass', views.CreatePassword.as_view(), name='createPassword'),
    path('loginoptions', views.LogIn.loginOptions, name='loginOptions'),
    path('customerlogin', views.CustomerLogins.as_view(), name='customerLogins'),
    path('createcustomeracc', views.CreateCustomerAccount.as_view(), name='createCustomerAccount'),
    path('generatenewpin', views.GenerateNewPin.as_view(), name='generateNewPin')
]