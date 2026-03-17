from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.http import HttpResponse
from django.views import generic
from django.db.transaction import atomic
from warehouseApp.models import Product, DiscountRate
from marketPlaceApp.models import CustomerAddToCart, DeliveryAddress, CurrentCartBatch, CustomerInfor
from businessApp.models import Business, BusinessBranch
from accountsApp.models import OnlineAccounts
from django.db.models import Q, ExpressionWrapper, Value, F, FloatField, Case, When, IntegerField, Value
from imageApp.models import Images, OtherFiles
from itertools import chain
import random as rd
import datetime as dt
from django.db.models import Sum, Count, Q


# Create your views here.

class GeneralMarket(generic.View):
    def get(self, request):
        search = request.GET.get('search')
        if not search:
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
        else:
            query = search or ''

            # Products
            products = Product.objects.filter(
                Q(disbleRef__productIsDisabled=False),
                Q(productName__icontains=query) |
                Q(productDescription__icontains=query) |
                Q(productCategory__icontains=query)
            ).annotate(
                obj=Value(2),
                generalDiscount=F('discountRate'),
                priceAfterDiscount=ExpressionWrapper(
                    F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') -
                    (((F('generalDiscount')/100) * F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice')) +
                    F('retailAndWholesaleRef__discountRef__discount')),
                    output_field=FloatField()
                ),
                match_score=(
                    Case(When(productName__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                    Case(When(productDescription__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                    Case(When(productCategory__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField())
                )
            ).order_by('-match_score')

            # Branches
            branches = BusinessBranch.objects.filter(
                Q(onlineVisibility=True),
                Q(branchName__icontains=query) |
                Q(branchType__icontains=query) |
                Q(branchAddress__icontains=query)
            ).annotate(
                obj=Value(1),
                match_score=(
                    Case(When(branchName__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                    Case(When(branchType__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                    Case(When(branchAddress__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField())
                )
            ).order_by('-match_score')

            # Businesses
            businesses = Business.objects.filter(
                Q(status=True),
                Q(busName__icontains=query) |
                Q(description__icontains=query)
            ).annotate(
                obj=Value(3),
                match_score=(
                    Case(When(busName__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField()) +
                    Case(When(description__icontains=query, then=Value(1)), default=Value(0), output_field=IntegerField())
                )
            ).order_by('-match_score')

            # Combine
            combinedResult = list(chain(products, branches, businesses))

            return render(request, 'marketPlace/generalMarket.html', {
                'products': products,
                'branches': branches,
                'businesses': businesses,
                'combinedResult': combinedResult
            })


    
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

            checkCurrentBatch = CurrentCartBatch.objects.filter(Q(customerTel=customerPhone) & Q(status='Waiting Payment Request')) 
            if checkCurrentBatch.exists():
                checkCurrentBatch = checkCurrentBatch[0]
            else:
                checkCurrentBatch = CurrentCartBatch()
                checkCurrentBatch.batchCode = f"{dt.datetime.today().year}{dt.datetime.today().month}{dt.datetime.today().day}{dt.datetime.today().hour}{dt.datetime.today().minute}{dt.datetime.today().second}{rd.randrange(1000,9999)}"
                checkCurrentBatch.customerTel = customerPhone
                checkCurrentBatch.save()

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
            # calculate discount
            d = float(product.retailAndWholesaleRef.currentCostPriceRef.unitSellingPrice) - float(product.priceAfterDiscount)

            db = CustomerAddToCart()
            db.branhRef = branch
            db.productRef = product
            db.customerTel = customerPhone
            db.unitPrice = product.priceAfterDiscount
            db.quantity = quantity
            db.discount = round(d * float(quantity), 2)
            db.totalPrice = round(float(product.priceAfterDiscount) * float(quantity), 2)
            db.orderID = rd.randrange(100000, 999999)
            db.batchCode = checkCurrentBatch.batchCode
            db.date = dt.datetime.now()
            db.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    
    # check carts
    def addedCarts(request, tel):
        carts = CustomerAddToCart.objects.filter(Q(customerTel=tel))
        totalPrice = 0.00
        for i in carts:
            totalPrice += float(i.totalPrice)
        totalPrice = round(totalPrice, 2)
        return render(request, 'marketPlace/customersCarts.html', {'carts': carts, 'totalPrice': totalPrice})
    
    # remove item from cart
    def removeItemFromCart(request, pk):
        cart = CustomerAddToCart.objects.get(Q(id=pk))
        cart.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        
    
    #  purchase hsitory
    def purchaseHistory(request, tel):
        carts = CustomerAddToCart.objects.filter(Q(customerTel=tel))
        return render(request, 'marketPlace/purchaseHistory.html', {'carts': carts})
    
    #request payment Page
    def paymentRequestPage(request, tel):
        carts = (CustomerAddToCart.objects.filter(Q(customerTel=tel))
                 .values('branhRef__branchName', 'branhRef__busRef__busName', 'branhRef__branchID', 'status', 'customerTel', 'batchCode')
                 .annotate(totalPrice=Sum('totalPrice')))
        return render(request, 'marketPlace/customerPayment.html', {'carts': carts})
    
    #request payment or cancel payment
    def requestPayment(request, batchCode):
        with atomic():
            customerTel = request.POST.get('customerTel')
            branchID = request.POST.get('branchID')
            branch = BusinessBranch.objects.get(Q(branchID=branchID))
            carts = CustomerAddToCart.objects.filter(Q(customerTel=customerTel) & Q(branhRef=branch) & Q(batchCode=batchCode))
            for cart in carts:
                bCode = CurrentCartBatch.objects.filter(Q(batchCode=batchCode) & Q(customerTel=cart.customerTel))
                if cart.status == 'Waiting Payment Request':
                    cart.status = 'Pending Payment Request'
                    # delete current batch code                
                    if bCode.exists():
                        bCode = bCode[0]
                        bCode.delete()
                    #cart.batchCode = batchCode
                else:
                    cart.status = 'Waiting Payment Request'
                    cart.batchCode = batchCode
                    # add the deleted batch code
                    if not bCode.exists():
                        bCode = CurrentCartBatch()
                        bCode.batchCode = batchCode
                        bCode.customerTel = cart.customerTel
                        bCode.save()
                cart.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    

    #payment methods and instructions
    def paymentInstructions(request, branchID, tel, batchCode):
        branch = BusinessBranch.objects.get(Q(branchID=branchID))
        requestAcceptanceCode = CustomerAddToCart.objects.filter(Q(customerTel=tel) & Q(branhRef=branch) & Q(batchCode=batchCode))
        if requestAcceptanceCode.exists():
            requestAcceptanceCode = requestAcceptanceCode[0].acceptedCode
        else:
            requestAcceptanceCode = ''        
        onlineAccounts = OnlineAccounts.objects.filter(Q(branchRef=branch))

        return render(request, 'marketPlace/paymentInstructions.html', {'accounts': onlineAccounts, 'acceptanceCode': requestAcceptanceCode, 'branch': branch})


#search item in general market =============================================
def autocomplete_items(request):
    query = request.GET.get('q', '')

    products = Product.objects.filter(
        Q(disbleRef__productIsDisabled=False),
        Q(productName__icontains=query) | Q(productDescription__icontains=query) | Q(productCategory__icontains=query)
    ).annotate(
        obj=Value(2),
        generalDiscount=F('discountRate'),
        priceAfterDiscount=ExpressionWrapper(
            F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') -
            (((F('generalDiscount')/100) * F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice')) +
             F('retailAndWholesaleRef__discountRef__discount')),
            output_field=FloatField()
        )
    ).order_by('?')

    branches = BusinessBranch.objects.filter(
        Q(onlineVisibility=True),
        Q(branchName__icontains=query) | Q(branchType__icontains=query) | Q(branchAddress__icontains=query)
    ).annotate(obj=Value(1)).order_by('?')

    # Businesses 
    businesses = Business.objects.filter(
        Q(status='Active'), 
        Q(busName__icontains=query) | Q(description__icontains=query)
    ).annotate(obj=Value(3)).order_by('?')

    combinedResult = list(chain(products, branches, businesses))
    rd.shuffle(combinedResult)

    results = []
    for obj in combinedResult[:10]:
        if hasattr(obj, 'productName'):
            results.append(obj.productName)
            results.append(obj.productDescription)
            results.append(obj.productCategory)
        elif hasattr(obj, 'branchName'):
            results.append(obj.branchName)
            results.append(obj.branchType)
            results.append(obj.branchAddress)
        elif hasattr(obj, 'busName'):
            results.append(obj.busName)
            results.append(obj.description)
    return JsonResponse(results, safe=False)


#search item in specific market =============================================
def autocomplete_items_specific_Market(request):
    query = request.GET.get('q', '')

    products = Product.objects.filter(
        Q(disbleRef__productIsDisabled=False),
        Q(productName__icontains=query) | Q(productDescription__icontains=query) | Q(productCategory__icontains=query)
    ).annotate(
        obj=Value(2),
        generalDiscount=F('discountRate'),
        priceAfterDiscount=ExpressionWrapper(
            F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') -
            (((F('generalDiscount')/100) * F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice')) +
             F('retailAndWholesaleRef__discountRef__discount')),
            output_field=FloatField()
        )
    ).order_by('?')

    branches = BusinessBranch.objects.filter(
        Q(onlineVisibility=True),
        Q(branchName__icontains=query) | Q(branchType__icontains=query) | Q(branchAddress__icontains=query)
    ).annotate(obj=Value(1)).order_by('?')


    combinedResult = list(chain(products, branches))
    rd.shuffle(combinedResult)

    results = []
    for obj in combinedResult[:10]:
        if hasattr(obj, 'productName'):
            results.append(obj.productName)
            results.append(obj.productDescription)
            results.append(obj.productCategory)
        elif hasattr(obj, 'branchName'):
            results.append(obj.branchName)
            results.append(obj.branchType)
            results.append(obj.branchAddress)
    return JsonResponse(results, safe=False)







    




