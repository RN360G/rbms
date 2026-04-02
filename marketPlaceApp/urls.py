from django.urls import path
from marketPlaceApp import views

urlpatterns = [
    path('', views.GeneralMarket.as_view(), name='generalMarket'),
    path('rn360b', views.GeneralMarket.specific, name='specifiMarket'),
    path('rn360b/<businessID>/<branchID>', views.InsideBusiness.as_view(), name="insideBuisness"),
    path('otherbranches/<branchID>', views.InsideBusiness.otherBranches, name='otherBranches'),
    path('aboutus/<branchID>', views.InsideBusiness.aboutUs, name='aboutUs'),
    path('rn360b_product/<branchID>/<productCode>', views.ProductDetails.as_view(), name='generalMarketProductDetails'),
    path('carts/<tel>/', views.ProductDetails.addedCarts, name='marketAddedCarts'),
    path('purchasehistory/<tel>/', views.ProductDetails.purchaseHistory, name='purchaseHistory'),
    path('removecustomeritemfromcart/<pk>', views.ProductDetails.removeItemFromCart, name='removeCustomerMarketCart'),
    path('paymentrequestpage/<tel>/', views.ProductDetails.paymentRequestPage, name='paymentRequestPage'),
    path('customerrequestpayment/<batchCode>', views.ProductDetails.requestPayment, name='customerRequestPayment'),
    path('paymentinstructions/<branchID>/<tel>/<batchCode>', views.ProductDetails.paymentInstructions, name='paymentInstructions'),
    path('autocomplete-items/', views.autocomplete_items, name='autocomplete_items'),
    path('autocomplete-items-specific-market/', views.autocomplete_items_specific_Market, name='autocomplete_items_specific_Market'),
    path('itsupport/', views.itSupport, name='itSupport'),
]
