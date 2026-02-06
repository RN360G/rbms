from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import generic
from warehouseApp.models import Product, DiscountRate
from businessApp.models import Business, BusinessBranch
from django.db.models import Q, ExpressionWrapper, Value, F


# Create your views here.


class GeneralMarket(generic.View):
    def get(self, request):
        products = Product.objects.filter(Q(disbleRef__productIsDisabled=False)).annotate(
                   generalDiscount= F('discountRate'),
                   #priceAfterDiscount=ExpressionWrapper(F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') - F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') * (Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount')))
                   priceAfterDiscount=F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') - F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') * (F('retailAndWholesaleRef__discountRef__discount'))
                   )
        branches = BusinessBranch.objects.filter(Q(onlineVisibility=True))

        return render(request, 'marketPlace/generalMarket.html', {'products': products, 'branches': branches})
    
    def post(self, request):
        return HttpResponse()
    


class AddBusiness(generic.View):
    def get(request):
        return render(request, 'businessApp/addBusiness.html')
    
    def post(request):
        return HttpResponse()
