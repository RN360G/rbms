from django.urls import path
from marketPlaceApp import views

urlpatterns = [
    path('', views.GeneralMarket.as_view(), name='generalMarket'),
    path('rn360b', views.GeneralMarket.specific, name='specifiMarket'),
    path('rn360b/<businessID>/<branchID>', views.InsideBusiness.as_view(), name="insideBuisness"),
    path('rn360b_product/<branchID>/<productCode>', views.ProductDetails.as_view(), name='generalMarketProductDetails'),
    path('carts/<tel>/', views.ProductDetails.addedCarts, name='marketAddedCarts'),
]
