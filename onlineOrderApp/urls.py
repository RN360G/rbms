from django.urls import path
from onlineOrderApp import views

urlpatterns = [
    path('', views.OnlineOrderManager.as_view(), name='onlineOrderManager'),
    path('customerorderitems/<tel>/<batchCode>', views.OnlineOrderManager.customerOrderItems, name='customerOrderItems'),
    path('confirmpaymentrequest', views.OnlineOrderManager.confirmPaymentRequest, name='confirmPaymentRequest'),
    path('confirmcustomerpayment', views.OnlineOrderManager.confirmPayment, name='confirmCustomerPayment'),
    path('reversetransactions', views.OnlineOrderManager.reverseTransaction, name='reverseTransaction'),
    path('packageanddeliver/<tel>/<batchCode>', views.OnlineOrderManager.packageAndDeliver, name='packageAndDeliver'), 

]
