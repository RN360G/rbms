from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponse
from django.views import generic
from django.db.transaction import atomic
from warehouseApp.models import Product, DiscountRate
from marketPlaceApp.models import CustomerAddToCart, DeliveryAddress
from businessApp.models import Business, BusinessBranch
from django.db.models import Q, ExpressionWrapper, Value, F, FloatField
from imageApp.models import Images, OtherFiles
from itertools import chain
import random as rd
import datetime as dt


# Create your views here.


class GeneralMarket(generic.View):
    def get(self, request):
        products = Product.objects.filter(Q(disbleRef__productIsDisabled=False)).annotate(
                   obj = Value(2),
                   generalDiscount= F('discountRate'),
                   priceAfterDiscount=ExpressionWrapper(
                                 F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') - (((F('generalDiscount')/100) * F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice')) + F('retailAndWholesaleRef__discountRef__discount')), output_field=FloatField())
                                 ).order_by('?')
        branches = BusinessBranch.objects.filter(Q(onlineVisibility=True)).annotate(obj = Value(1)).order_by('?')
        combinedResult = list(chain(products, branches))
        rd.shuffle(combinedResult)
        return render(request, 'marketPlace/generalMarket.html', {'products': products, 'branches': branches, 'combinedResult': combinedResult})
    
    # specify whether product, business or all
    def specific(self, request, opt):
        products = Product.objects.filter(Q(disbleRef__productIsDisabled=False)).annotate(
                   obj = Value(2),
                   generalDiscount= F('discountRate'),
                   priceAfterDiscount=ExpressionWrapper(
                                 F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') - (((F('generalDiscount')/100) * F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice')) + F('retailAndWholesaleRef__discountRef__discount')), output_field=FloatField())
                                 ).order_by('?')
        branches = BusinessBranch.objects.filter(Q(onlineVisibility=True)).annotate(obj = Value(1)).order_by('?')
        if opt == 'products':
             combinedResult = products
        elif opt == 'business':
            combinedResult = branches
        elif opt == 'all':
            combinedResult = list(chain(products, branches))
        rd.shuffle(combinedResult)
        return render(request, 'marketPlace/generalMarket.html', {'products': products, 'branches': branches, 'combinedResult': combinedResult})
    

class InsideBusiness(generic.View):
    def get(self, request, businessID, branchID):
        branch = BusinessBranch.objects.get(Q(branchID=branchID))
        products = None
        if branch.branchType == 'Retail & Wholesale Business':            
            generalDiscount = DiscountRate.objects.filter(Q(busRef=branch.busRef))
            if generalDiscount.exists():
                generalDiscount = generalDiscount[0].discount
            else:
                generalDiscount = 0.00

            products = Product.objects.filter(Q(busRef__busID=businessID) & Q(retailAndWholesaleRef__branchRef=branch) &
               Q(disbleRef__productIsDisabled=False) & Q(retailAndWholesaleRef__isVisibleOnline=True)).annotate(
                    totalDiscaount=ExpressionWrapper(Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount'), output_field=FloatField()),
                    priceAfterDiscount= F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') - F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') * (Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount'))
                   )
        elif branch.branchType == 'Hotel':
            pass
        return render(request, 'marketPlace/insideTheBusiness.html', {'products': products, 'branch': branch})
    
    def post(self, request, businessID, branchID):
        return HttpResponse()


# product details
class ProductDetails(generic.View):
    def get(self, request, branchID, productCode):
        branch = BusinessBranch.objects.get(Q(branchID=branchID))
        generalDiscount = DiscountRate.objects.filter(Q(busRef=branch.busRef))
        if generalDiscount.exists():
            generalDiscount = generalDiscount[0].discount
        else:
            generalDiscount = 0.00

        flyer = Images.objects.filter(Q(subjectID=productCode))
        if flyer.exists():
            flyer = flyer[0]

        otherImages = OtherFiles.objects.filter(Q(imageRef__busRef = branch.busRef) & Q(imageRef__subjectID=productCode))

        product = (
            Product.objects
            .annotate(
                totalDiscount=ExpressionWrapper(
                    Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount'),
                    output_field=FloatField()
                ),
                priceAfterDiscount=ExpressionWrapper(
                    F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') -
                    F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') *
                    (Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount')),
                    output_field=FloatField()
                )
            ).get(
                Q(busRef__busID=branch.busRef.busID) &
                Q(retailAndWholesaleRef__branchRef=branch) &
                Q(productCode=productCode) &
                Q(disbleRef__productIsDisabled=False) &
                Q(retailAndWholesaleRef__isVisibleOnline=True)
            )
        )

        
        return render(request, 'marketPlace/productDetails.html', {'product': product, 'flyer': flyer, 'otherImages': otherImages, 'branch': branch})
    
    def post(self, request, branchID, productCode):
        with atomic():
            quantity = request.POST.get('quantity')
            customerPhone = request.POST.get('customerPhone')
            branch = BusinessBranch.objects.get(Q(branchID=branchID))
            generalDiscount = DiscountRate.objects.filter(Q(busRef=branch.busRef))
            if generalDiscount.exists():
                generalDiscount = generalDiscount[0].discount
            else:
                generalDiscount = 0.00
            product = (
                Product.objects
                .annotate(
                    totalDiscount=ExpressionWrapper(
                        Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount'),
                        output_field=FloatField()
                    ),
                    priceAfterDiscount=ExpressionWrapper(
                        F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') -
                        F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') *
                        (Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount')),
                        output_field=FloatField()
                    )
                ).get(
                    Q(busRef__busID=branch.busRef.busID) &
                    Q(retailAndWholesaleRef__branchRef=branch) &
                    Q(productCode=productCode) &
                    Q(disbleRef__productIsDisabled=False) &
                    Q(retailAndWholesaleRef__isVisibleOnline=True)
                )
            )

            db = CustomerAddToCart()
            db.branhRef = branch
            db.productRef = product
            db.customerTel = customerPhone
            db.unitPrice = product.priceAfterDiscount
            db.quantity = quantity
            db.totalPrice = round(float(product.priceAfterDiscount) * float(quantity))
            db.status=  'Pending'
            db.orderID = rd.randrange(100000, 999999)
            db.date = dt.datetime.now()
            db.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    
    # check carts
    def addedCarts(request, tel):
        carts = CustomerAddToCart.objects.filter(Q(customerTel=tel))
        return render(request, 'marketPlace/customersCarts.html', {'carts': carts})
    



