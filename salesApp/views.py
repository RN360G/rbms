from django.shortcuts import render, redirect
from django.views import generic
from warehouseApp.models import Product, DisabledProducts, DiscountRate
from businessApp.models import Printers, AssignPrinterToUser
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from loginAndOutApp.views import loginSessions, dashboardMenuAccess
from django.db.models import Q, F, Value, FloatField, ExpressionWrapper, Count
from django.db.models.functions import ExtractYear, ExtractMonth
from salesApp.models import RetailAndWholesale, CurrentCostAndPrice, RetailWholesalesTally, ReturnAmountToCustomer, ReturnedProductsRecord, StockAdjustment, CustomMeasuringUnit, MeasuringUnits, Quantities, AddToCart, TransactionIDs
from salesApp.models import RetailAndWholesaleCustomers, CustomerPayments, CustomerItemsPurchased, ProductSuppliers, SupplyQuantityRecords, TempSupplyQuantity, TemporalPurchaseDetails, SalesRecords, AdvancePaymentItems, AdvancePaymentItemsDetails
from salesApp.models import CashOnhand, PaymentAgreement, PaymentAgreementDetails, AgreementConfirmationCode, ExcludeDays, DatesForPayments, CustomerOwingDetails, AllCustomerTransactions, IndividualItemsSupplied
from businessApp.models import BusinessBranch
from accountsApp.views import accountTransactions
from accountsApp.models import OperationExpenses, OversAndShortagesRecord
from salesApp.models import DiscountRate as IndividualDiscount
from imageApp.models import Images, OtherFiles
from django.db.transaction import atomic
import datetime as dt
from imageApp.views import ImageUpload
from django.contrib import messages
from usersApp.views import activityLogs, haveAccess
from django.db.transaction import atomic
from django.contrib.auth.hashers import check_password
from itertools import chain
import random as rd
from sms import sendSMS
import pytz
from django.db.models import Sum
from escpos.printer import Usb, Network, Serial, Dummy, LP, Win32Raw, File



# Create your views here.

def products(request):
    if not haveAccess(request, '3'):
        messages.set_level(request, messages.WARNING)
        messages.warning(request, {'message': 'You do not have access to warehouse management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
        return render(request, 'user/state.html')   
         
    dashboardMenuAccess(request)
    access = {'3':haveAccess(request, '3'), 
              '300':haveAccess(request, '300'),
              '301':haveAccess(request, '301'), 
              '303':haveAccess(request, '303'), 
              '307':haveAccess(request, '307'), 
              '308':haveAccess(request, '308'), 
              '309':haveAccess(request, '309'),
              '311':haveAccess(request, '311'), 
              '312':haveAccess(request, '312'),
              '313':haveAccess(request, '313'), 
              '314':haveAccess(request, '314'), 
              '315':haveAccess(request, '315'),
            }
    
    products = Product.objects.filter(Q(busRef=loginSessions(request, 'business')) & 
                                      Q(retailAndWholesaleRef__branchRef=loginSessions(request, 'branch')) & 
                                      Q(disbleRef__productIsDisabled=False))
    restockAlerts = Product.objects.filter(Q(busRef=loginSessions(request, 'business')) & 
                                           Q(retailAndWholesaleRef__branchRef=loginSessions(request, 'branch')) & 
                                           Q(disbleRef__productIsDisabled=False) & 
                                           Q(retailAndWholesaleRef__quantityRef__packQty__lte=F('retailAndWholesaleRef__reorderLevel')) & 
                                           Q(retailAndWholesaleRef__reorderLevel__gt=0))
    disabled = Product.objects.filter(Q(busRef=loginSessions(request, 'business')) & 
                                      Q(retailAndWholesaleRef__branchRef=loginSessions(request, 'branch')) & 
                                      Q(disbleRef__productIsDisabled=True))    
    meassureUnits = CustomMeasuringUnit.objects.filter(Q(bussRef=loginSessions(request, 'business')) & Q(branchRef=loginSessions(request, 'branch'))).order_by('-id')

    discount = 0.00  
    discount = DiscountRate.objects.filter(Q(busRef=loginSessions(request, 'business')))
    if discount.exists():
        discount = discount[0].discount
    else:
        disc = DiscountRate()
        disc.busRef = loginSessions(request, 'business')
        disc.addedBy = loginSessions(request, 'user')
        disc.discount = 0.00
        disc.save()
    if request.user_agent.is_mobile:
        return render(request, 'sales/productsMobile.html', {'products': products, 'uAccess':access, 'disabledProducts': disabled, 'measureUnits': meassureUnits, 'discount': discount, 'restockAlerts': restockAlerts})
    else:
        return render(request, 'sales/products.html', {'products': products, 'uAccess':access, 'disabledProducts': disabled, 'measureUnits': meassureUnits, 'discount': discount, 'restockAlerts': restockAlerts})


class AddProduct(generic.View):
    def get(self, request): 
        dashboardMenuAccess(request) 
        return render(request, 'sales/products.html')
    
    def post(self, request):
        if not haveAccess(request, '300'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to Add Product page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        # process the form data here
        productName = request.POST.get('productName')
        description = request.POST.get('description')
        category = request.POST.get('category')

        measureUnitStocked = request.POST.get('measureUnitStocked')
        measureUnitSold = request.POST.get('measureUnitSold')

        quantity = request.POST.get('quantity')
        quantityPerPack = request.POST.get('quantityPerPack')
        qtyLeftLessThanPack = request.POST.get('qtyLeftLessThanPack')

        costPricePack = request.POST.get('costPricePack')
        costPriceUnit = request.POST.get('costPriceUnit')

        sellingPricePack = request.POST.get('sellingPricePack')
        sellingPriceUnit = request.POST.get('sellingPriceUnit')

        with atomic():
            product = None 
            check_product_exist= Product.objects.filter(Q(busRef__busID=loginSessions(request, 'business').busID) & Q(branhRef=loginSessions(request, 'branch')) &  Q(productName=productName))
            if not check_product_exist.exists():
                priceCost = CurrentCostAndPrice()                
                if measureUnitStocked == 'Piece' or (measureUnitStocked == measureUnitSold):
                    priceCost.costPrice = costPricePack
                    priceCost.unitCostPrice= costPricePack
                    priceCost.sellingPrice = sellingPricePack
                    priceCost.unitSellingPrice = sellingPricePack
                else:
                    priceCost.costPrice = costPricePack
                    priceCost.unitCostPrice= costPriceUnit
                    priceCost.sellingPrice = sellingPricePack
                    priceCost.unitSellingPrice = sellingPriceUnit
                priceCost.save()

                measureUnit = MeasuringUnits()
                if measureUnitStocked == 'Piece':
                    measureUnit.soldUnit = 'Piece'
                else:
                    measureUnit.soldUnit = measureUnitSold
                measureUnit.stockedUnit = measureUnitStocked                
                measureUnit.save()

                qtyModel = Quantities()
                qtyModel.qtyPerPack = quantityPerPack
                qtyModel.packQty = quantity
                qtyModel.uintQty = float(quantity) * float(quantityPerPack) + float(qtyLeftLessThanPack)
                qtyModel.save()
                # =========================================================================================

                retailWholesale = RetailAndWholesale()
                retailWholesale.branchRef = loginSessions(request, 'branch')
                retailWholesale.currentCostPriceRef = priceCost
                retailWholesale.measureRef = measureUnit
                retailWholesale.quantityRef = qtyModel
                retailWholesale.save()
                
                productCode = '100001'
                lastProductCode = Product.objects.filter(Q(busRef__busID=loginSessions(request, 'business').busID))
                if lastProductCode.exists():
                    productCode = lastProductCode.order_by('-id')[0].productCode
                    productCode = int(productCode) + 1 

                disableProduct = DisabledProducts()
                disableProduct.branchRef = loginSessions(request, 'branch')
                disableProduct.operationBy = loginSessions(request, 'user')
                disableProduct.date = dt.datetime.now()
                disableProduct.save()

                product = Product()
                product.busRef = loginSessions(request, 'business')
                product.productName = productName
                product.productCode = productCode 
                product.productDescription = description
                product.productCategory = category
                product.measureUnit = measureUnit
                product.belongsToModel = loginSessions(request, 'branch').branchType
                product.addedBy = loginSessions(request, 'user')
                product.dateAdded = dt.datetime.now()
                product.retailAndWholesaleRef = retailWholesale
                product.disbleRef = disableProduct
                product.save()

                tally = RetailWholesalesTally()
                tally.retailAndWholesaleRef = retailWholesale
                tally.transactionType = 'In'
                tally.transactionBy = loginSessions(request, 'user')
                tally.quantity = retailWholesale.quantityRef.packQty
                tally.balance = retailWholesale.quantityRef.packQty
                tally.unitQuantity = retailWholesale.quantityRef.uintQty
                tally.uintBalance = retailWholesale.quantityRef.uintQty
                tally.narration = 'Stock available by the time of this product was registered'
                tally.date = dt.datetime.now()
                tally.save()

                # set intial value of the individual to 0.00
                individualDiscount = IndividualDiscount()
                individualDiscount.branchRef = loginSessions(request, 'branch')
                individualDiscount.productRef = product
                individualDiscount.discount = 0.00
                individualDiscount.isActive = True
                individualDiscount.startFrom = dt.datetime.now()
                individualDiscount.endAt = dt.datetime.now()
                individualDiscount.addedBy = loginSessions(request, 'user')
                individualDiscount.save()
                product.retailAndWholesaleRef.discountRef = individualDiscount
                product.retailAndWholesaleRef.save()

                activityLogs(request, loginSessions(request, 'user').userID, 'Added a new Product', 'You add a new product called ' 
                             + str(productName) + ' with code: ' + 
                             str(productCode) + 'with initial stock of ' + str(quantity) + ' ' + str(measureUnit))
                return redirect('warehouse')            
            else:
                return HttpResponse('product Exists')            

    def addUnits(request):
        with atomic():
            unitName= request.POST.get('unitName')
            unitCategory = request.POST.get('unitCategory')
            unit = CustomMeasuringUnit()
            unit.bussRef = loginSessions(request, 'business')
            unit.branchRef = loginSessions(request, 'branch')
            unit.unit = unitName
            unit.unityType = unitCategory
            unit.save()
        return redirect(to='salesProduct')
        
    def deleteUnit(request, pk):
        with atomic():
            unit = CustomMeasuringUnit.objects.get(Q(id=pk))
            unit.delete()
        return redirect(to='salesProduct')


class SetProductProperties(generic.View):
    def get(self, request, pk):
        dashboardMenuAccess(request)
        access = {'3':haveAccess(request, '3'), 
              '300':haveAccess(request, '300'),
              '301':haveAccess(request, '301'), 
              '303':haveAccess(request, '303'), 
              '307':haveAccess(request, '307'), 
              '308':haveAccess(request, '308'), 
              '309':haveAccess(request, '309'),
              '311':haveAccess(request, '311'), 
              '312':haveAccess(request, '312'),
              '313':haveAccess(request, '313'), 
              '314':haveAccess(request, '314'), 
              '315':haveAccess(request, '315'),
              '316':haveAccess(request, '316'),
        }
        product = Product.objects.get(Q(id=pk))
        tally = RetailWholesalesTally.objects.filter(Q(retailAndWholesaleRef=product.retailAndWholesaleRef)).order_by('-id')
        adjustments = StockAdjustment.objects.filter(Q(retailAndWholesaleRef=product.retailAndWholesaleRef)).order_by('-id')
        discount = IndividualDiscount.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(productRef=product))
        otherImages = OtherFiles.objects.filter(Q(imageRef__busRef = loginSessions(request, 'business')) & Q(imageRef__subjectID=product.productCode))
        image = Images.objects.filter(Q(subjectID=product.productCode) & Q(busRef=loginSessions(request, 'business')))
        if image.exists():
            image = image[0]
        if request.user_agent.is_mobile:
            return render(request, 'sales/setPropertiesMobile.html', {'product': product, 'tally': tally, 'uAccess':access, 'adjustments': adjustments, 'discount': discount, 'image': image, 'otherImages': otherImages})
        else:
            return render(request, 'sales/setProperties.html', {'product': product, 'tally': tally, 'uAccess':access, 'adjustments': adjustments, 'discount': discount, 'image': image, 'otherImages': otherImages})


    # set price of the product
    def setPrice(request, pk):
        if not haveAccess(request, '303'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to change price.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        with atomic():
            sellingPrice = request.POST.get('sellingPrice')
            unitSellingPrice = request.POST.get('unitSellingPrice')
            costPrice = request.POST.get('costPrice')
            unitCostPrice = request.POST.get('unitCostPrice')
            product = Product.objects.get(Q(id=pk))
            if product.retailAndWholesaleRef.measureRef.stockedUnit == 'Piece' and product.retailAndWholesaleRef.measureRef.soldUnit == 'Piece' or product.retailAndWholesaleRef.measureRef.stockedUnit == product.retailAndWholesaleRef.measureRef.soldUnit: 
                product.retailAndWholesaleRef.currentCostPriceRef.costPrice = costPrice
                product.retailAndWholesaleRef.currentCostPriceRef.sellingPrice = sellingPrice
                product.retailAndWholesaleRef.currentCostPriceRef.unitSellingPrice = sellingPrice 
                product.retailAndWholesaleRef.currentCostPriceRef.unitCostPrice = costPrice
            else:
                product.retailAndWholesaleRef.currentCostPriceRef.costPrice = costPrice
                product.retailAndWholesaleRef.currentCostPriceRef.sellingPrice = sellingPrice
                product.retailAndWholesaleRef.currentCostPriceRef.unitCostPrice = unitCostPrice
                product.retailAndWholesaleRef.currentCostPriceRef.unitSellingPrice = unitSellingPrice
            product.retailAndWholesaleRef.currentCostPriceRef.save()
            activityLogs(request, loginSessions(request, 'user').userID, 'Set Price and Cost', f'You set the selling price and cost price of {product.productName} ({product.productCode}) to {sellingPrice} and {costPrice} respectively')
            return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))
    
    
    # general discount
    def generalDiscount(request):
        if not haveAccess(request, '308'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to set general discount.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        with atomic():
            discount = request.POST.get('discount')
            r = float(discount)/100
            rate = round(r, 2)
            db = DiscountRate.objects.filter(Q(busRef=loginSessions(request, 'business')))
            if db.exists():
                db = db[0]
                db.discount = rate
                db.addedBy = loginSessions(request, 'user')
                db.save()
            else:
                db = DiscountRate()
                db.busRef = loginSessions(request, 'business')
                db.discount = rate
                db.addedBy = loginSessions(request, 'user')
                db.save()
            products = Product.objects.filter(Q(busRef=loginSessions(request, 'business')))
            for product in products:
                product.discountRate = discount
                product.save()
        return redirect('salesProduct') 
    

    # individual discount on products under individual branches
    def individualDiscount(request, pk):
        if not haveAccess(request, '309'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to set individual product discount.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        with atomic():
            discount = request.POST.get('discount')
            fromDate = request.POST.get('fromDate')
            endAt = request.POST.get('endAt')
            format_string = '%Y-%m-%dT%H:%M'

            startD = dt.datetime.strptime(fromDate, format_string)
            endD = dt.datetime.strptime(endAt, format_string)
            
            product = Product.objects.get(Q(id=pk))

            disc = float(discount)/100
            disc = round(disc, 2)

            db = IndividualDiscount.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(productRef=product))
            db.branchRef = loginSessions(request, 'branch')
            db.productRef = product
            if startD >= endD:
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'Start period cannot be greater or equal the the end perion', 'title': 'Wrong Date Selections'}, extra_tags='salesStartAndEndDate')
                return render(request, 'sales/state.html', {'productID':product.id})
            db.startFrom = startD
            db.endAt = endD
            db.isActive = False
            db.addedBy = loginSessions(request, 'user')
            db.discountSwaper = disc
            db.discount = 0.00
            db.save()
            product.retailAndWholesaleRef.discountRef = db
            product.retailAndWholesaleRef.save()
        return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))

    
    # set minimum and online order
    def minimumAndOnlineOrder(request, pk):
        if not haveAccess(request, '315'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to set product online visibility.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        with atomic():
            onlineOder = request.POST.get('onlineOder')
            minOrder = request.POST.get('minOrder')
            
            product = Product.objects.get(Q(id=pk))
            if onlineOder == 'enable':
                product.retailAndWholesaleRef.enableOnlineOrder = True
            else:
                product.retailAndWholesaleRef.enableOnlineOrder = False
            product.retailAndWholesaleRef.minimumOrder = minOrder
            product.retailAndWholesaleRef.save()        
            activityLogs(request, loginSessions(request, 'user').userID, 'online and mim order', f'Changed online and minimum order of the product: {product.productName} ({product.productCode})') 
        return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))

    # restock level of the product
    def setRestockLevel(request, pk):
        if not haveAccess(request, '312'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to set restock level.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        with atomic():
            restock = request.POST.get('restock')
            product = Product.objects.get(Q(id=pk))
            product.retailAndWholesaleRef.reorderLevel = restock
            product.retailAndWholesaleRef.save()
            activityLogs(request, loginSessions(request, 'user').userID, 'Set Restock Level', f'You set the restock level of {product.productName} ({product.productCode}) to {restock}')
        return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))
    
    # set return period
    def setReturnPeriod(request, pk):
        if not haveAccess(request, '316'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to set return period.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        with atomic():
            returnPeriod = request.POST.get('returnPeriod')
            product = Product.objects.get(Q(id=pk))
            product.retailAndWholesaleRef.returnPeriod = returnPeriod
            product.retailAndWholesaleRef.save()
            activityLogs(request, loginSessions(request, 'user').userID, 'Set Return Period', f'You set the return period of {product.productName} ({product.productCode}) to {returnPeriod} days')
        return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))
    
    # add to the current stock
    def addStock(request, pk):
        if not haveAccess(request, '301'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to add stock.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        with atomic():
            quantity = request.POST.get('quantity')
            additionalQuantity = request.POST.get('additionalQuantity')
            costPrice = request.POST.get('costPrice')
            unitCostPrice = request.POST.get('unitCostPrice')
            
            product = Product.objects.get(Q(id=pk))
            tally = RetailWholesalesTally()
            tally.retailAndWholesaleRef = product.retailAndWholesaleRef            

            if product.retailAndWholesaleRef.measureRef.stockedUnit == 'Piece' and product.retailAndWholesaleRef.measureRef.soldUnit == 'Piece' or product.retailAndWholesaleRef.measureRef.stockedUnit == product.retailAndWholesaleRef.measureRef.soldUnit:                
                
                product.retailAndWholesaleRef.quantityRef.packQty += float(quantity)
                product.retailAndWholesaleRef.quantityRef.uintQty = product.retailAndWholesaleRef.quantityRef.packQty

                product.retailAndWholesaleRef.currentCostPriceRef.costPrice = costPrice 
                product.retailAndWholesaleRef.currentCostPriceRef.unitCostPrice = costPrice

                tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                tally.uintBalance = tally.balance
                tally.quantity = quantity
                tally.unitQuantity = quantity
                tally.narration = f"Added to the stock {quantity} {product.retailAndWholesaleRef.measureRef.stockedUnit}"
                activityLogs(request, loginSessions(request, 'user').userID, 'Added a stock', f'You added a stock of {quantity} to the product: {product.productName} ({product.productCode})')
            else:
                qty = (float(quantity) * float(product.retailAndWholesaleRef.quantityRef.qtyPerPack)) + float(additionalQuantity)
                product.retailAndWholesaleRef.quantityRef.uintQty += qty 
                product.retailAndWholesaleRef.quantityRef.packQty = int(float(product.retailAndWholesaleRef.quantityRef.uintQty) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))                
                
                product.retailAndWholesaleRef.currentCostPriceRef.costPrice = costPrice 
                product.retailAndWholesaleRef.currentCostPriceRef.unitCostPrice = unitCostPrice                
                
                tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                tally.uintBalance = product.retailAndWholesaleRef.quantityRef.uintQty
                tally.quantity = quantity
                tally.unitQuantity = qty
                tally.narration = f"Added to the stock {quantity} {product.retailAndWholesaleRef.measureRef.stockedUnit}/{qty} {product.retailAndWholesaleRef.measureRef.soldUnit}"               
                activityLogs(request, loginSessions(request, 'user').userID, 'Added a stock', f'You added a stock of {quantity}/{qty} to the product: {product.productName} ({product.productCode})')
                
            product.retailAndWholesaleRef.currentCostPriceRef.save()
            product.retailAndWholesaleRef.quantityRef.save()

            tally.transactionType = 'In'
            tally.transactionBy = loginSessions(request, 'user')            
            tally.date = dt.datetime.now()
            tally.save()            
            return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))
    
    # upload Image
    def uploadImage(request, pk):
        if not haveAccess(request, '313'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to change product image.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        with atomic():
            product = Product.objects.get(Q(id=pk))
            file = request.FILES['upload']
            image = ImageUpload()
            #image.upload(file, subjectID=product.productCode)
            imageRef = image.uploadProductFlyer(request, file, product.productCode)
            product.productImageRef = imageRef
            product.save()
            activityLogs(request, loginSessions(request, 'user').userID, 'Product Image', f'You uploaded an image to the product: {product.productName} ({product.productCode})')        
        return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))
    
    # upload other images
    def uploadOtherProductImages(request, pk):
        if not haveAccess(request, '313'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to change product image.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        with atomic():
            product = Product.objects.get(Q(id=pk))
            file = request.FILES['upload']
            image = ImageUpload()
            #image.upload(file, subjectID=product.productCode)
            image.uploadProductImages(request, file, product.productCode)
            activityLogs(request, loginSessions(request, 'user').userID, 'Product Image', f'You uploaded an image to the product: {product.productName} ({product.productCode})')        
        return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))

    
    # set online visibilty 
    def setOnlineVisibility(request, pk):
        if not haveAccess(request, '315'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to set product online visibility.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        with atomic():
            visibility = request.POST.get('visibility')
            product = Product.objects.get(Q(id=pk))
            if visibility == 'Online':
                product.retailAndWholesaleRef.isVisibleOnline = True
            else:
                product.retailAndWholesaleRef.isVisibleOnline = False
            product.retailAndWholesaleRef.save()        
            activityLogs(request, loginSessions(request, 'user').userID, 'Product online visibility', f'You changed the online visibility of the product {product.productName} ({product.productCode}) to {visibility}') 
        return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))
        
    # adjust stock
    def stockAdjustment(request, pk):
        if not haveAccess(request, '311'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to adjust product stock.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        with atomic():
            product = Product.objects.get(Q(id=pk))
            adjustmentType = request.POST.get('adjustmentType')
            quantity = request.POST.get('quantity')
            narration = request.POST.get('narration')

            oldStock = float(product.retailAndWholesaleRef.quantityRef.packQty)
            oldStockUnit = float(product.retailAndWholesaleRef.quantityRef.uintQty)

            tally = RetailWholesalesTally()
            adjustment = StockAdjustment()

            if adjustmentType == "Wrong Entry (Add Stock)" or adjustmentType == "Found Lost Products":
                if product.retailAndWholesaleRef.measureRef.stockedUnit == 'Piece' and product.retailAndWholesaleRef.measureRef.soldUnit == 'Piece' or product.retailAndWholesaleRef.measureRef.stockedUnit == product.retailAndWholesaleRef.measureRef.soldUnit:
                    product.retailAndWholesaleRef.quantityRef.packQty += float(quantity)
                    product.retailAndWholesaleRef.quantityRef.uintQty += float(quantity)
                    tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                    tally.uintBalance = tally.balance
                    tally.quantity = quantity
                    tally.unitQuantity = quantity
                else:
                    product.retailAndWholesaleRef.quantityRef.uintQty = float(product.retailAndWholesaleRef.quantityRef.uintQty) + float(quantity) 
                    product.retailAndWholesaleRef.quantityRef.packQty = int(float(product.retailAndWholesaleRef.quantityRef.uintQty) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                    tally.uintBalance = product.retailAndWholesaleRef.quantityRef.uintQty
                    tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                    tally.quantity = int(float(quantity) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                    tally.unitQuantity = quantity
                tally.narration = 'Add to the stock ' + str(quantity) + ' ' + product.retailAndWholesaleRef.measureRef.stockedUnit
                tally.transactionType = 'Adjustment(In)'
                adjustment.transactionType = "In"                
            else:
                if float(quantity) > float(product.retailAndWholesaleRef.quantityRef.uintQty):
                    messages.set_level(request, messages.ERROR)
                    messages.error(request, {'message': 'The quantity to be removed from the stock is more than total quantity in stock', 'title': 'Wrong Quantity'}, extra_tags='salesAdjustmentQtyMoreThanQtyInStock')
                    return render(request, 'sales/state.html', {'productID': str(product.id)})                
                else:
                    if product.retailAndWholesaleRef.measureRef.stockedUnit == 'Piece' and product.retailAndWholesaleRef.measureRef.soldUnit == 'Piece' or product.retailAndWholesaleRef.measureRef.stockedUnit == product.retailAndWholesaleRef.measureRef.soldUnit:
                        product.retailAndWholesaleRef.quantityRef.packQty -= float(quantity)
                        product.retailAndWholesaleRef.quantityRef.uintQty -= float(quantity)
                        tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                        tally.uintBalance = tally.balance
                        tally.quantity = quantity
                        tally.unitQuantity = quantity
                    else:
                        product.retailAndWholesaleRef.quantityRef.uintQty = float(product.retailAndWholesaleRef.quantityRef.uintQty) - float(quantity) 
                        product.retailAndWholesaleRef.quantityRef.packQty = int(float(product.retailAndWholesaleRef.quantityRef.uintQty) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                        tally.uintBalance = product.retailAndWholesaleRef.quantityRef.uintQty
                        tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                        tally.quantity = int(float(quantity) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                        tally.unitQuantity = quantity
                    tally.narration = 'Remove from the stock ' + str(quantity) + ' ' + product.retailAndWholesaleRef.measureRef.stockedUnit
                    tally.transactionType = 'Adjustment(Out)'
                    adjustment.transactionType = "Out"   

            #product.retailAndWholesaleRef.save() 
            product.retailAndWholesaleRef.quantityRef.save()       
            tally.retailAndWholesaleRef = product.retailAndWholesaleRef
            tally.quantity = quantity            
            tally.transactionBy = loginSessions(request, 'user')            
            tally.date = dt.datetime.now()
            tally.save()
            
            # record the adjusted stocks
            adjustment.adjustmentType = adjustmentType
            adjustment.retailAndWholesaleRef = product.retailAndWholesaleRef
            adjustment.quantity = quantity
            adjustment.oldStock = oldStock
            adjustment.oldStockUnit = oldStockUnit
            adjustment.newStockUnit = product.retailAndWholesaleRef.quantityRef.uintQty
            adjustment.newStock = product.retailAndWholesaleRef.quantityRef.packQty
            adjustment.narration = narration
            adjustment.transactionBy = loginSessions(request, 'user')
            adjustment.date = dt.datetime.now()
            adjustment.save()
            activityLogs(request, loginSessions(request, 'user').userID, 'Stock Adjustment', f'You adjusted the stock of the product {product.productName} ({product.productCode}) from {oldStock}/{oldStockUnit} to {adjustment.newStock}/{adjustment.newStockUnit} with the reason: {narration}') 
            return HttpResponseRedirect('/sales/salesproductproperties/' + str(product.id))


    # disabled product cannot be visible or available for sales
    def disableProduct(request):
        if not haveAccess(request, '307'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to disable products.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        productCode = request.POST.get('productCode')
        with atomic():
            check = Product.objects.filter(Q(productCode=productCode) & Q(busRef=loginSessions(request, 'business')) & Q(disbleRef__productIsDisabled=False))
            if check.exists():
                product = check[0]
                product.disbleRef.productIsDisabled = True
                product.disbleRef.save()
            else:
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'Wrong product code. Operation failed.', 'title': 'Product not found'}, extra_tags='salesProductDisableWrongProductCode')
                return render(request, 'sales/state.html')
            activityLogs(request, loginSessions(request, 'user').userID, 'Disabled Product', f'You disabled the product : {product.productName} ({product.productCode})')  
        return redirect(to='salesProduct')    

    # enabled product can be visible or available for sales
    def enableProduct(request, pk):
        with atomic():
            product = Product.objects.get(Q(id=pk))
            product.disbleRef.productIsDisabled = False
            product.disbleRef.save()
            activityLogs(request, loginSessions(request, 'user').userID, 'Anabled Product', f'You anabled the product : {product.productName} ({product.productCode})')  
        return redirect(to='salesProduct')
    

# customer management =============================================================================
class Customers(generic.View):
    def get(self, request):
        if not haveAccess(request, '11'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to customer management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        customers = RetailAndWholesaleCustomers.objects.filter(Q(branchRef=loginSessions(request, 'branch'))).order_by('-totalAmountOwed', '-id')
        return render(request, 'sales/customers.html', {'customers': customers})
    
    def post(self, request):
        customerName = request.POST.get('customerName')
        address = request.POST.get('address')
        tel = request.POST.get('tel')

        tel = str(tel)
        tel = tel[1:]
        tel = f'+233{tel}'
        
        with atomic():
            check_customer_exist= RetailAndWholesaleCustomers.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(customerContact=tel))
            if check_customer_exist.exists():
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'Customer with the same phonenumber already exists', 'title': 'Customer Exists'}, extra_tags='salesCustomerExists')
                return render(request, 'sales/state.html')
            
            customer = RetailAndWholesaleCustomers()
            customer.branchRef = loginSessions(request, 'branch')
            customer.customerName = customerName
            customer.customerAddress = address
            customer.customerContact = tel
            customer.save()
            activityLogs(request, loginSessions(request, 'user').userID, 'Customer Added', f'You added a cutomer with name : {customerName} and telephone number: {tel}')  
        return redirect(to='salesCustomers')      

    def cusstomerDetails(request, pk):
        dashboardMenuAccess(request)
        customer = RetailAndWholesaleCustomers.objects.get(pk=pk)       
        customerTransactions  = AllCustomerTransactions.objects.filter(Q(customerRef=customer) & Q(customerRef__branchRef=loginSessions(request, 'branch'))).order_by('-id')
        oweFromOtherBranches = SalesRecords.objects.values('branchRef__branchName', 'branchRef__branchID').filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(customerRef__customerContact=customer.customerContact)).annotate(Sum('amountOwe')).annotate(Sum('amountToPay')).annotate(Sum('amountPaid'))
        forthisBranch = SalesRecords.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(customerRef=customer))
        totalOweForThis = forthisBranch.aggregate(Sum('amountOwe'))['amountOwe__sum']
        forAllBranches = SalesRecords.objects.filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(customerRef__customerContact=customer.customerContact))
        totalOweForAll = forAllBranches.aggregate(Sum('amountOwe'))['amountOwe__sum']
        advancePayitems = AdvancePaymentItems.objects.filter(Q(customerRef=customer) & Q(branchRef=loginSessions(request, 'branch')) & ~Q(quatity=0))
        advancePayTotalPrice = advancePayitems.aggregate(Sum('totalPrice'))['totalPrice__sum']
        return render(request, 'sales/customerDetails.html', {'customer': customer, 'transactions': customerTransactions, 'oweOtherBranches': oweFromOtherBranches, 'allBranch': totalOweForAll, 'thisBranch': totalOweForThis, 'advancePayitems': advancePayitems, 'advancePayTotalPrice': advancePayTotalPrice})
    
    # debit and credit customer amount owe
    def customerOwe(request, transactionID, customerTel, inOut, amount):
        customer = RetailAndWholesaleCustomers.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(customerContact=customerTel))
        if customer.exists():
            customer = customer.last()
            with atomic():
                if inOut == 'Owed':
                    customer.totalAmountOwed += amount
                elif inOut == 'Paid':
                    customer.totalAmountOwed -= amount
                else:
                    pass
            customer.save()

            details = CustomerOwingDetails()
            details.customerRef = customer
            details.transactionID = transactionID
            details.operationType = inOut
            details.amount = amount
            details.balance = customer.totalAmountOwed
            details.date = dt.datetime.now()
            details.save()   


# Supplier management ================================================================================================
class Suppliers(generic.View):
    def get(self, request):
        if not haveAccess(request, '12'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to suppliers management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        suppliers = ProductSuppliers.objects.filter(Q(branchRef=loginSessions(request, 'branch'))).order_by('-amountOwed', '-id')        
        return render(request, 'sales/suppliers.html', {'suppliers': suppliers})
    
    def post(self, request):
        tel = request.POST.get('tel')
        supplierName = request.POST.get('supplierName')
        address = request.POST.get('address')
        with atomic():
            check_supplier_exist= ProductSuppliers.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(supplierContact=request.POST.get('tel')))
            if check_supplier_exist.exists():
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'Supplier with the same details already exists', 'title': 'Supplier Exists'}, extra_tags='salesSupplierExists') 
                return render(request, 'sales/state.html')
            else:
                supplier = ProductSuppliers()
                supplier.branchRef = loginSessions(request, 'branch')
                supplier.supplierName = supplierName
                supplier.supplierContact = tel
                supplier.supplierAddress = address
                supplier.save()
            activityLogs(request, loginSessions(request, 'user').userID, 'Supplier Added', f'You added a supplier with name : {supplierName} and telephone number: {tel}')  
        return redirect(to='salesSuppliers')
        
    def supplierDetails(request, pk):
        dashboardMenuAccess(request)
        suppliers = ProductSuppliers.objects.get(Q(id=pk))
        products = Product.objects.filter(Q(busRef=loginSessions(request, 'business')) & 
                                      Q(retailAndWholesaleRef__branchRef=loginSessions(request, 'branch')) & 
                                      Q(disbleRef__productIsDisabled=False))
        suppliesRecords = SupplyQuantityRecords.objects.filter(Q(supplierRef=suppliers)).order_by('-id')
        tempSupplyItems = TempSupplyQuantity.objects.filter(Q(supplierRef=suppliers) & Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))

        context = {
            'products': products,
            'supplier': suppliers,
            'suppliesRecords': suppliesRecords,
            'tempSupplyItems': tempSupplyItems
            }
        if request.user_agent.is_mobile:
            return render(request, 'sales/supplierDetailsMobile.html', context)
        else:
            return render(request, 'sales/supplierDetails.html', context) 
        
    # save supply records
    def supplyRecords(request):  
        if not haveAccess(request, '12'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to supplier management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        pk = request.POST.get('supplierID')
        supplier = ProductSuppliers.objects.get(Q(id=pk))      
        products = request.POST.getlist('product')
        qty = request.POST.getlist('qty')
        cost = request.POST.getlist('cost')
        totalCost = request.POST.get('totalCost')
        amount = request.POST.get('amount')
        owe = request.POST.get('owe')
        receiptNumber = request.POST.get('receiptNumber')
        narration = request.POST.get('narration')

        with atomic():
            # store amount owe
            supplier.amountOwed += float(totalCost) - float(amount)          

            sup = SupplyQuantityRecords()
            sup.branchRef = loginSessions(request, 'branch')
            sup.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().second}{loginSessions(request, 'user').userID}{rd.randrange(1000, 9999)}"
            sup.supplierRef = supplier
            sup.transactionType = 'Supply'
            sup.receiptNumber = receiptNumber
            sup.totalCost = totalCost
            sup.amountPaid = amount
            sup.Balance = supplier.amountOwed
            sup.supplyDate  = dt.datetime.now()
            sup.narration = narration
            sup.receivedBy = loginSessions(request, 'user') 
            sup.setAmountOwe()           

            n = 0 
            getUnitCostTotal = 0       
            for proID in products:
                q = qty[n]
                c = cost[n]
                getUnitCostTotal += float(q) * float(c) 
                print(float(c) * float(q))
                print(proID)
                n = n + 1
            
            if getUnitCostTotal != float(totalCost):
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'Summation of total unit cost do not match the total cost entered', 'title': 'Unit cost total should be equal to total cost'}, extra_tags='unitCostDonnotMatchTotalCost')
                return render(request, 'sales/state.html', {'supplierID': supplier.id})
            
            if float(totalCost)-float(amount) != float(owe):
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'The value entered in amount owe is not correct. When you subtract amount paid from total cost should be equal to amount owe.', 'title': 'Amount Owe is not correct'}, extra_tags='incorrectAmountOwe')
                return render(request, 'sales/state.html', {'supplierID': supplier.id})
            
            else:
                n = 0 
                getUnitCostTotal = 0 
                supplier.save()
                sup.save()          
                for proID in products:
                    product = Product.objects.get(Q(productCode=proID))
                    q = qty[n]
                    c = cost[n]
                    getUnitCostTotal += float(q) * float(c) 
                    n = n + 1

                    idv = IndividualItemsSupplied()
                    idv.productRef = product
                    idv.supplyRef = sup
                    idv.qty = float(q)
                    idv.unityCost = float(c)   
                    idv.totalCost = float(q) * float(c)
                    if idv.totalCost > 0:
                        idv.save() 
                        temp = TempSupplyQuantity.objects.filter(Q(productRef__productCode=proID) & Q(supplierRef=supplier) & Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))    
                        temp.delete()
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
    # save suppliers payments
    def repaySuppliers(request):
        if not haveAccess(request, '12'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to suppliers management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        pk = request.POST.get('supplierID')
        optType = request.POST.get('optType')
        amount = request.POST.get('amount')
        receipt = request.POST.get('receipt')
        narration = request.POST.get('narration')
        supplier = ProductSuppliers.objects.get(Q(id=pk)) 

        with atomic():
            # store amount owe
            sup = SupplyQuantityRecords()
            if float(amount) > float(supplier.amountOwed):
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'Amount to be paid cannot be greater than amount owe', 'title': 'Amount Owe is less than amount Paid'}, extra_tags='amountOweCannotBeGreaterThanAmountPaid')
                return render(request, 'sales/state.html', {'supplierID': supplier.id})

            if optType == 'Repayment':
                supplier.amountOwed -= float(amount) 
                sup.transactionType = 'Repayment'
            else:
                supplier.amountOwed += float(amount)
                sup.transactionType = 'Reversed Repayment'
            supplier.save()

            sup.branchRef = loginSessions(request, 'branch')
            sup.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().second}{loginSessions(request, 'user').userID}{rd.randrange(1000, 9999)}"
            sup.supplierRef = supplier            
            sup.receiptNumber = receipt
            sup.totalCost = 0
            sup.amountPaid = amount
            sup.amountOwe = supplier.amountOwed
            sup.Balance = supplier.amountOwed
            sup.supplyDate  = dt.datetime.now()
            sup.narration = narration
            sup.receivedBy = loginSessions(request, 'user') 
            sup.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    
    #supplies items details
    def suppliesItemsDetails(request, sup, pk):
        supplierRecord = SupplyQuantityRecords.objects.get(Q(id=pk)) 
        inds = IndividualItemsSupplied.objects.filter(Q(supplyRef=supplierRecord))        
        with atomic():            
            products = Product.objects.filter(Q(retailAndWholesaleRef__branchRef=loginSessions(request, 'branch')) & Q(disbleRef__productIsDisabled=False))
            tempSupplyQuantity = TempSupplyQuantity.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
            for p in products:
                check = tempSupplyQuantity.filter(Q(productRef=p))
                if not check.exists():
                    temp = TempSupplyQuantity()
                    temp.branchRef = loginSessions(request, 'branch')
                    temp.userRef = loginSessions(request, 'user')
                    temp.productRef = p
                    temp.save()
        return render(request, 'sales/supplierItems.html', {'individualItems': inds, 'sup': sup, 'supplierRecord': supplierRecord})
    
    # get all items for supply record
    def generateItemsForSupplyRecord(request, pk):
        with atomic():          
            supplier = ProductSuppliers.objects.get(Q(id=pk))  
            products = Product.objects.filter(Q(retailAndWholesaleRef__branchRef=loginSessions(request, 'branch')) & Q(disbleRef__productIsDisabled=False))
            tempSupplyQuantity = TempSupplyQuantity.objects.filter(Q(supplierRef=supplier) & Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
            for p in products:
                check = tempSupplyQuantity.filter(Q(productRef=p))
                if not check.exists():
                    temp = TempSupplyQuantity()
                    temp.branchRef = loginSessions(request, 'branch')
                    temp.userRef = loginSessions(request, 'user')
                    temp.productRef = p
                    temp.supplierRef = supplier                    
                    temp.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
             

    #Disable wrong transaction
    def disableWrongTransaction(request):
        if not haveAccess(request, '12'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to suppliers management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        transID = request.POST.get('transID')
        supplierID = request.POST.get('supplierID')
        supplier = ProductSuppliers.objects.get(Q(id=supplierID))
        check = SupplyQuantityRecords.objects.filter(Q(transactionID=transID) & Q(transactionType='Supply'))
        if check.exists():
            check = check.last()
            check.isDisabled = True
            check.save()           
            supplier.amountOwed -= check.amountOwe
            supplier.save()

            # store the evidence of the reversed supply
            sup = SupplyQuantityRecords()
            sup.branchRef = loginSessions(request, 'branch')
            sup.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().second}{loginSessions(request, 'user').userID}{rd.randrange(1000, 9999)}"
            sup.supplierRef = supplier
            sup.transactionType = 'Reversed Supply'
            sup.receiptNumber = check.receiptNumber
            sup.totalCost = check.totalCost
            sup.amountPaid = check.amountPaid
            sup.amountOwe = check.amountOwe
            sup.Balance = supplier.amountOwed
            sup.supplyDate  = dt.datetime.now()
            sup.narration = f"Reversed supply with transaction ID: {check.transactionID} and receipt Number: {check.receiptNumber} with amount {check.amountOwe} owing reversed."
            sup.receivedBy = loginSessions(request, 'user') 
            sup.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.set_level(request, messages.ERROR)
            messages.error(request, {'message': 'You are see this error message because of one of the following reasons: 1) Wrong transaction ID. 2) The transaction type is not "Supply"', 'title': 'Wrong transaction ID or The transaction type is not Supply'}, extra_tags='wrongTransactionIDOrTransactionTypeIsNotSupply')
            return render(request, 'sales/state.html', {'supplierID': supplier.id})        

    # store temporary supply quantity before saving the supply record
    def storeTemporarySupply(request):
        productCode= request.POST.get('productCode')
        quantity = request.POST.get('qty')        
        cost = request.POST.get('cost')
        print(cost)
        supplierKey = request.POST.get('supplierKey')
        opt = request.POST.get('opt')
        supplier = ProductSuppliers.objects.get(Q(id=supplierKey))
        check = TempSupplyQuantity.objects.filter(Q(productRef__productCode=productCode) & Q(supplierRef=supplier) & Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
        if opt == 'add':
            if check.exists():
                temp = check[0]
                temp.qty = quantity
                temp.unityCost = cost
                temp.totalCost = round(float(quantity) * float(cost), 2)
                temp.save()
            else:
                temp = TempSupplyQuantity()
                temp.productRef = Product.objects.get(Q(productCode=productCode) & Q(busRef=loginSessions(request, 'business')))
                temp.supplierRef = supplier
                temp.branchRef = loginSessions(request, 'branch')
                temp.userRef = loginSessions(request, 'user')
                temp.qty = quantity
                temp.unityCost = cost
                temp.totalCost = round(float(quantity) * float(cost), 2)
                temp.save()
        else:
            if check.exists():
                check.delete()
        return JsonResponse({'quantity': quantity, 'cost': cost})
    
    # display temporary supply quantity before saving the supply record
    def displayTemporarySupply(request):
        supplierKey = request.GET.get('supplier')
        supplier = ProductSuppliers.objects.get(Q(id=supplierKey))
        tempSupplies = TempSupplyQuantity.objects.filter(Q(supplierRef=supplier) & Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
        data = []
        for temp in tempSupplies:
            data.append({
                'productCode': temp.productRef.productCode,
                'productName': temp.productRef.productName,
                'quantity': temp.qty,
                'cost': temp.unityCost,
                'totalCost': float(temp.qty) * float(temp.unityCost)
            })
        return JsonResponse({'tempSupplies': data})   


# selling page
class Selling(generic.View):    
    transactionID = None
    def get(self, request):
        if not haveAccess(request, '6'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to sell product to customer.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        checkActiveTransaction = TransactionIDs.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')) & Q(isSelcted=True))
        if checkActiveTransaction.exists():
            self.transactionID = checkActiveTransaction[0].transactionID
        else:
            self.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().second}{loginSessions(request, 'user').userID}{rd.randrange(1000, 9999)}" 
        cash = CashOnhand.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
        totalTransaction = 0
        if cash.exists():
            totalTransaction = cash[0].totalTransaction
            cash = cash[0].cash            
        else:
            cash = 0.00
        generalDiscount = DiscountRate.objects.filter(Q(busRef=loginSessions(request, 'business')))
        if generalDiscount.exists():
            generalDiscount = generalDiscount[0].discount
        else:
            generalDiscount = 0.00
        data = Product.objects.filter(Q(busRef=loginSessions(request, 'business')) & Q(retailAndWholesaleRef__branchRef=loginSessions(request, 'branch')) &
               Q(disbleRef__productIsDisabled=False)).annotate(
                   totalDiscaount=ExpressionWrapper(Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount'), output_field=FloatField()),
                   priceAfterDiscount= F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') - F('retailAndWholesaleRef__currentCostPriceRef__unitSellingPrice') * (Value(generalDiscount) + F('retailAndWholesaleRef__discountRef__discount'))
                   )
        
        # activate or deactivate discount in individual discount
        indDisc = IndividualDiscount.objects.filter(Q(branchRef=loginSessions(request, 'branch')))
        if indDisc.exists():            
            nowDate = dt.datetime.strptime(str(dt.datetime.now(pytz.utc)), '%Y-%m-%d %H:%M:%S.%f%z')       
            for dis in indDisc:
                if nowDate >= dis.startFrom and nowDate < dis.endAt:
                    d = float(dis.discountSwaper)
                    dis.isActive = True
                    dis.discount = d                
                    dis.save()
                elif nowDate > dis.startFrom and nowDate >= dis.endAt:
                    dis.isActive = False
                    dis.discount = 0.00
                    dis.discountSwaper = 0.00
                    dis.save()
                else:
                    pass
        if request.user_agent.is_mobile:
            return render(request, 'sales/sellMobile.html', {'data': data, 'transactionID': self.transactionID, 'cashOnHand': cash, 'totalTransaction': totalTransaction, 'generalDiscount': generalDiscount})
        else:
            return render(request, 'sales/sell.html', {'data': data, 'transactionID': self.transactionID, 'cashOnHand': cash, 'totalTransaction': totalTransaction, 'generalDiscount': generalDiscount})
    
    # add items to cart
    def addToCart(request):
        if not haveAccess(request, '6'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to sell product to customer.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        productCode = request.POST.get('productCode')
        quantity = request.POST.get('quantity')
        opt = request.POST.get('opt')
        transactionID = request.POST.get('transactionID')
        
        with atomic():
            product = Product.objects.get(Q(busRef=loginSessions(request, 'business')) & Q(disbleRef__productIsDisabled=False) & Q(productCode=productCode))            
            check_cart = AddToCart.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                                  Q(productRef=product) & Q(transactionBy=loginSessions(request, 'user')) & 
                                                  Q(transactionID=transactionID))
            checkTemPurchase = TemporalPurchaseDetails.objects.filter(Q(transactionID=transactionID) & Q(branchRef=loginSessions(request, 'branch')))

            generalDiscount = DiscountRate.objects.filter(Q(busRef=loginSessions(request, 'business')))
            if generalDiscount.exists():
                generalDiscount = generalDiscount[0].discount
            else:
                generalDiscount = 0.00

            # get the sum of general discount and the individual discount
            totalDiscount = float(product.retailAndWholesaleRef.discountRef.discount) + generalDiscount
            
            temPurchase = None
            if checkTemPurchase.exists():
                temPurchase = checkTemPurchase[0]
            else:
                temPurchase = TemporalPurchaseDetails()
                temPurchase.branchRef = loginSessions(request, 'branch')
                temPurchase.transactionID = transactionID
                temPurchase.totalPrice = 0.00
                temPurchase.amountToPay = 0.00
                temPurchase.discount = 0.00
                temPurchase.save()
            if opt == 'add':                
                if check_cart.exists():
                    cart = check_cart[0]  
                    cart.quantity += float(quantity)                    
                    # check if the quantity to add is more than quantity in stock
                    outOfStock = 'No'
                    if float(cart.quantity) > float(product.retailAndWholesaleRef.quantityRef.uintQty) or float(quantity) > float(product.retailAndWholesaleRef.quantityRef.uintQty):
                        pass
                    else:                                      
                        cart.discount = float(cart.pricePerItem) * totalDiscount * float(cart.quantity)            
                        cart.totalPrice = float(cart.quantity) * float(cart.pricePerItem) - float(cart.discount)
                        cart.save()
                else:
                    # check if the quantity to add is more than quantity in stock
                    outOfStock = 'No'
                    if float(quantity) > float(product.retailAndWholesaleRef.quantityRef.uintQty):
                        pass
                    else:
                        cart = AddToCart()
                        cart.transactionID = transactionID
                        cart.branchRef = loginSessions(request, 'branch')
                        cart.transactionBy = loginSessions(request, 'user')
                        cart.productRef = product
                        cart.quantity = float(quantity)
                        cart.pricePerItem = product.retailAndWholesaleRef.currentCostPriceRef.unitSellingPrice
                        cart.discount = float(cart.pricePerItem) * totalDiscount * float(cart.quantity)                    
                        cart.totalPrice = float(cart.quantity) * float(cart.pricePerItem) - float(cart.discount)
                        cart.save()
            elif opt == 'remove':
                if check_cart.exists():
                    cart = check_cart[0]
                    # check if the quantity to remove is more than quantity in cart
                    if float(quantity) > float(cart.quantity):
                        return JsonResponse({'error': 'Quantity to remove is more than quantity in cart'})
                    cart.quantity -= float(quantity)
                    if cart.quantity <= 0:
                        cart.delete()
                    else:
                        cart.discount = float(cart.pricePerItem) * totalDiscount * float(cart.quantity) 
                        cart.totalPrice = float(cart.quantity) * float(cart.pricePerItem) - float(cart.discount)
                        cart.save()       

            allCarts = AddToCart.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                                Q(transactionBy=loginSessions(request, 'user')) & 
                                                Q(transactionID=transactionID))            
            # store total price of all items purchase 
            totalPrice = 0.00
            for cart in allCarts:
                totalPrice += float(cart.totalPrice)

            temPurchase.totalPrice = totalPrice
            temPurchase.amountToPay = totalPrice
            temPurchase.discount = totalDiscount
            temPurchase.save()

            carts = list(AddToCart.objects.values('transactionID', 'productRef__productCode', 'pricePerItem', 'quantity', 'totalPrice', 'productRef__retailAndWholesaleRef__measureRef__stockedUnit', 'productRef__retailAndWholesaleRef__measureRef__soldUnit').filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                            Q(productRef=product) & Q(transactionBy=loginSessions(request, 'user')) & 
                                            Q(transactionID=transactionID)))
            return JsonResponse({'data':carts})
        

    # display all items added to cart
    def displayAllCart(request):
        transactionID = request.GET.get('transactionID')
        carts = list(AddToCart.objects.values('transactionID', 'productRef__productCode', 'pricePerItem', 
                                              'quantity', 'totalPrice', 'productRef__retailAndWholesaleRef__measureRef__stockedUnit', 
                                              'productRef__retailAndWholesaleRef__measureRef__soldUnit').filter(
                                                Q(branchRef=loginSessions(request, 'branch')) &                                                                                                                                                                                                                                                                                               
                                                Q(transactionBy=loginSessions(request, 'user')) & 
                                                Q(transactionID=transactionID)))
        return JsonResponse({'data':carts})
    

    # display total amount 
    def totalAmountInCart(request):
            transactionID = request.GET.get('transactionID')
            """totalAmount = AddToCart.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                                Q(transactionBy=loginSessions(request, 'user')) & 
                                                Q(transactionID=transactionID)).aggregate(Sum('totalPrice'))['totalPrice__sum'] or 0.0"""
            totalAmount = 0.0
            amtToPay = 0.0
            carts = AddToCart.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                            Q(transactionBy=loginSessions(request, 'user')) &
                                            Q(transactionID=transactionID))
            for cart in carts:
                totalAmount += float(cart.totalPrice)   
                amtToPay += float(cart.totalPrice)
            return JsonResponse({'totalAmount': totalAmount, 'amtToPay': amtToPay})
    

    # display transaction on hold
    def displayTransactionOnHold(request):
        transactions = TransactionIDs.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user'))).order_by('-id')
        return render(request, 'sales/transactions.html', {'transactions': transactions})
    
    # change the status of a transaction ID
    def selectTransaction(request, pk, action):
        with atomic():
            transaction = TransactionIDs.objects.get(Q(id=pk))
            allTrans = TransactionIDs.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
            
            if action == 'activate':
                transaction.isSelcted = True
            elif action == 'onHold':
                transaction.isSelcted = False
            transaction.save()

            for trans in allTrans:
                if not trans == transaction:
                    trans.isSelcted = False            
                trans.save()
        return redirect('salesSelling')
    
    # put a transaction to hold by saving its id
    def saveTransactionID(request):
        transID = request.POST.get('transactionID')
        carts = AddToCart.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                            Q(transactionBy=loginSessions(request, 'user')) &
                                            Q(transactionID=transID))        
        if carts.exists():            
            check_transactionID = TransactionIDs.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                                                Q(userRef=loginSessions(request, 'user')) & 
                                                                Q(transactionID=transID))
            if not check_transactionID.exists():
                transactionID = TransactionIDs()
                transactionID.branchRef = loginSessions(request, 'branch')
                transactionID.userRef = loginSessions(request, 'user')
                transactionID.transactionID = transID
                transactionID.save()
                return redirect('salesSelling')
            else:
                messages.set_level(request, messages.INFO)
                messages.error(request, {'message': 'A Transaction ID is activated, new transaction cannot be '
                'started. Please click of select transaction button and put the active transaction to hold.', 
                'title': 'Transaction ID Activated'}, extra_tags='transactionAlreadyActivates') 
                return render(request, 'sales/state.html')
        else:
            messages.set_level(request, messages.INFO)
            messages.error(request, {'message': 'This transaction cannot be put to hold, no item is added to cart. '
                'Please make sure at least one item is added', 
                'title': 'No Item is added'}, extra_tags='noItemIsAddedToCart') 
            return render(request, 'sales/state.html')        
    
    def deleteTransactionID(request, pk):
        with atomic():
            transaction = TransactionIDs.objects.get(Q(id=pk))
            transaction.delete()
            temps = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=transaction.transactionID))
            temps.delete()
            carts = AddToCart.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                            Q(transactionBy=loginSessions(request, 'user')) &
                                            Q(transactionID=transaction.transactionID))
            for cart in carts:
                cart.delete()
        return redirect('transactionOnHold')
    
    # all current items added to cart
    def currentCart(request, transID):
        with atomic():
            carts = AddToCart.objects.annotate(priceWithoutDiscount = F('pricePerItem') * F('quantity')).filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                                Q(transactionBy=loginSessions(request, 'user')) &
                                                Q(transactionID=transID))
            totalAmt = 0.00
            for cart in carts:
                totalAmt += cart.totalPrice
            if carts.exists():
                check_transactionID = TransactionIDs.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                                                        Q(userRef=loginSessions(request, 'user')) & 
                                                                        Q(transactionID=transID))
                if not check_transactionID.exists():
                    transactionID = TransactionIDs()
                    transactionID.branchRef = loginSessions(request, 'branch')
                    transactionID.userRef = loginSessions(request, 'user')
                    transactionID.transactionID = transID
                    transactionID.save()                    
                transaction = TransactionIDs.objects.get(Q(transactionID=transID))  
                transaction.isSelcted = True               
                transaction.save()
                return render(request, 'sales/currentCarts.html', {'carts': carts, 'totalAmt': totalAmt}) 
            else:
                return redirect('salesSelling') 

    # delete particular item Added to cart
    def deleteParticularItemAddedToCart(request, pk):        
        cart = AddToCart.objects.get(Q(id=pk))
        temps = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=cart.transactionID))
        cart.delete()
        return HttpResponseRedirect('/sales/salescurrentitemsaddedtocart/' + str(cart.transactionID))

    
# make payment to items bought
class Payment(generic.View):
    def get(self, request):
        if not haveAccess(request, '6'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to sell product to customer.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        # save the current transaction ID if not save
        tID = request.GET.get('transID')
        transID = None
        if tID != None:
            request.session['transID'] = tID
            transID = tID
        else:
            transID = request.session['transID']
        carts = AddToCart.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                            Q(transactionBy=loginSessions(request, 'user')) &
                                            Q(transactionID=transID))
        if carts.exists():
            with atomic():
                check_transactionID = TransactionIDs.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                                                Q(userRef=loginSessions(request, 'user')) & 
                                                                Q(transactionID=transID))
                if not check_transactionID.exists():
                    transactionID = TransactionIDs()
                    transactionID.branchRef = loginSessions(request, 'branch')
                    transactionID.userRef = loginSessions(request, 'user')
                    transactionID.transactionID = transID
                    transactionID
                    transactionID.isSelcted = True
                    transactionID.save()
                else:
                    transaction = TransactionIDs.objects.get(Q(transactionID=transID))
                    transaction.isSelcted = True
                    transaction.save()        

                # make sure all active IDs for this user is inactive except the current ID
                allTrans = TransactionIDs.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
                for trans in allTrans:
                    if not trans.transactionID == transID:
                        trans.isSelcted = False            
                    trans.save()
            temp = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=transID, ))    
            customerList = RetailAndWholesaleCustomers.objects.filter(Q(branchRef__busRef=loginSessions(request, 'business')))   
            if request.user_agent.is_mobile:
                return render(request, 'sales/makePaymentMobile.html', {'temp': temp, 'customerList': customerList})   
            else:                   
                return render(request, 'sales/makePayment.html', {'temp': temp, 'customerList': customerList})
        else:
            messages.set_level(request, messages.INFO)
            messages.error(request, {'message': 'Payment is not possible when no item is added to cart. '
                'Please make sure at least one item is added', 
                'title': 'No Item is added'}, extra_tags='noItemIsAddedToCart')
            return render(request, 'sales/state.html')        

    def post(self, request):
        if not haveAccess(request, '6'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to sell product to customer.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        customers = RetailAndWholesaleCustomers.objects.filter(Q(branchRef=loginSessions(request, 'branch'))).order_by('-totalAmountOwed', '-id')
        paymentTerm = request.POST.get('paymentTerm')        
        transactionID = request.POST.get('transactionID')
        name = request.POST.get('name')
        tel = request.POST.get('tel')
        payAmount = request.POST.get('payAmount')

        request.session['paymentTerm'] = paymentTerm
        request.session['transactionID'] = transactionID
        request.session['custName'] = name
        request.session['custTel'] = tel
        request.session['payAmount'] = payAmount
        request.session['paymentTermShort'] = ''
        
                
        if paymentTerm == 'Part payment (PP)':
            request.session['paymentTermShort'] = 'PP'
            if request.user_agent.is_mobile:
                return render(request, 'sales/paymentAgreementMobile.html', {'payTerm': 'PP', 'transactionID': transactionID})  
            else:
                return render(request, 'sales/paymentAgreement.html', {'payTerm': 'PP', 'transactionID': transactionID})
        
        elif paymentTerm == 'Advance payment (AP)':
            request.session['paymentTermShort'] = 'AP'    
            if request.user_agent.is_mobile:
                return render(request, 'sales/paymentAgreementMobile.html', {'payTerm': 'AP', 'customer': customers})  
            else:   
                return render(request, 'sales/paymentAgreement.html', {'payTerm': 'AP', 'customer': customers})
        
        elif paymentTerm == 'Installment agreements (IA)':
            request.session['paymentTermShort'] = 'IA'
            if request.user_agent.is_mobile:
                return render(request, 'sales/paymentAgreementMobile.html', {'payTerm': 'IA', 'customer': customers})  
            else:
                return render(request, 'sales/paymentAgreement.html', {'payTerm': 'IA', 'customer': customers})        
        else:
            if not payAmount:
                temp = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=transactionID)) 
                payAmount = float(temp.amountToPay)
                request.session['paymentTermShort'] = 'FP'
            Payment.savePayment(request, transactionID, paymentTerm, payAmount, name, tel)
            return redirect('salesSelling')
        

    # confirm agreement code
    def confirmAgreementCode(request):
        temp = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=request.session['transactionID']))
        # for part payment        
        numOfDays = request.POST.get('numberOfDays')       

        #for installement agreement
        period = request.POST.get('period')
        days = request.POST.getlist('days')
        amountPerPeriod = request.POST.get('amountPerPeriod')
        numberOfPeriod = request.POST.get('numberOfPeriod')

        panelty = request.POST.get('panelty')  
        opt = ''
        # store confirmation code
        checkCode = AgreementConfirmationCode.objects.filter(Q(transactionID=str(request.session['transactionID'])))        
        if not checkCode.exists(): 
            #for installement agreement
            request.session['period'] = period
            #request.session['amountPerPeriod'] = amountPerPeriod   
            request.session['numberOfPeriod'] = numberOfPeriod
            
            # IA ======================================================================================================================================
            if str(request.session['paymentTerm']) == 'Installment agreements (IA)':                
                request.session['panelty'] = panelty
                request.session['paymentTermShort'] = 'IA'
                daysInterpretation = ''
                
                numberOfDays = 0
                if period == 'Daily':
                    amount = round(float(temp.amountToPay) / float(numberOfPeriod), 2)
                    request.session['amountPerPeriod'] = amount
                    daysInterpretation = f"{numberOfPeriod} Day(s). Amount to be paid every day: {amount}"
                    request.session['numberOfDays'] = numberOfPeriod                   
                elif period == 'Weekly':
                    amount = round(float(temp.amountToPay) / float(numberOfPeriod), 2)
                    request.session['amountPerPeriod'] = amount
                    daysInterpretation = f"{numberOfPeriod} Week(s). Amount to be paid every week: {amount}" 
                    request.session['numberOfDays'] = int(numberOfPeriod) * 7   
                elif period == 'Monthly':
                    amount = round(float(temp.amountToPay) / float(numberOfPeriod), 2)
                    request.session['amountPerPeriod'] = amount
                    daysInterpretation = f"{numberOfPeriod} Month(s). Amount to be paid every month: {amount}" 
                    request.session['numberOfDays'] = int(numberOfPeriod) * 30   
                elif period == 'Yearly':
                    amount = round(float(temp.amountToPay) / float(numberOfPeriod), 2)
                    request.session['amountPerPeriod'] = amount
                    daysInterpretation = f"{numberOfPeriod} Year(s). Amount to be paid every year: {amount}"   
                    request.session['numberOfDays'] = int(numberOfPeriod) * 365

                

                agreeCode = AgreementConfirmationCode.objects.filter(Q(transactionID=str(request.session['transactionID']))).last()
                excludes = ExcludeDays.objects.filter(Q(transactionID=request.session['transactionID']))
                #delete all existing days 
                for ex in excludes:
                    ex.delete()
                # add new days
                for day in days: 
                    exclude = ExcludeDays()
                    exclude.transactionID = request.session['transactionID']
                    exclude.days = day
                    exclude.save()
               
                # store agreement code for IA    
                today = str(dt.date.today())
                today = dt.datetime.strptime(today, "%Y-%m-%d")
                dateGiven = today + dt.timedelta(days=int(request.session['numberOfDays']))
                # check exclude days from ExcludeDays Table
                with atomic():
                    code  = AgreementConfirmationCode()
                    code.code = f"{rd.randrange(1000,9999)}{rd.randrange(1000,9999)}{rd.randrange(10,99)}"
                    code.branchRef = loginSessions(request, 'branch')
                    code.transactionID = request.session['transactionID']
                    code.customerContact = request.session['custTel']
                    code.save()                     
                    panelty = (float(panelty)/100) * temp.amountToPay
                    panelty = round(panelty, 2)
                    agreeCode = AgreementConfirmationCode.objects.filter(Q(transactionID=str(request.session['transactionID']))).last().code 
                    sendSMS(str(request.session['custTel']), f'{request.session['paymentTerm']} Agreement. You must settle this payment in {daysInterpretation}. You will pay a panelty of {panelty} if you breach this contract. By Mentioning the: {agreeCode} to the officer to confirm means you have agreed to the contract.') 
                    print(f'{request.session['paymentTerm']} Agreement. You must settle this payment in {daysInterpretation}. You will pay a panelty of {panelty} if you breach this contract. By Mentioning the: {agreeCode} to the officer to confirm means you have agreed to the contract.')
            
            # store agreement code for PP
            # PP ======================================================================================================================================
            elif str(request.session['paymentTerm']) == 'Part payment (PP)': 
                request.session['numberOfDays'] = numOfDays
                request.session['panelty'] = panelty
                request.session['paymentTermShort'] = 'PP'
                today = str(dt.date.today())
                today = dt.datetime.strptime(today, "%Y-%m-%d")
                dateGiven = today + dt.timedelta(days=int(request.session['numberOfDays']))
                with atomic():
                    code  = AgreementConfirmationCode()
                    code.code = f"{rd.randrange(1000,9999)}{rd.randrange(1000,9999)}{rd.randrange(10,99)}"
                    code.branchRef = loginSessions(request, 'branch')
                    code.transactionID = request.session['transactionID']
                    code.customerContact = request.session['custTel']
                    code.save() 
                    temp = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=request.session['transactionID']))
                    panelty = (float(panelty)/100) * temp.amountToPay
                    panelty = round(panelty, 2)
                    agreeCode = AgreementConfirmationCode.objects.filter(Q(transactionID=str(request.session['transactionID']))).last().code 
                    sendSMS(str(request.session['custTel']), f'{request.session['paymentTerm']} Agreement. You must settle this payment in {numOfDays} days. The last date to settle your debt is ({dateGiven}). You will pay a panelty of {panelty} if you breach this contract. By Mentioning the: {agreeCode} to the officer to confirm means you have agreed to the contract.') 
          
           # AP ======================================================================================================================================
            elif str(request.session['paymentTerm']) == 'Advance payment (AP)':
                request.session['numberOfDays'] = numOfDays
                request.session['panelty'] = panelty
                request.session['paymentTermShort'] = 'AP'
                with atomic():
                    code  = AgreementConfirmationCode()
                    code.code = f"{rd.randrange(1000,9999)}{rd.randrange(1000,9999)}{rd.randrange(10,99)}"
                    code.branchRef = loginSessions(request, 'branch')
                    code.transactionID = request.session['transactionID']
                    code.customerContact = request.session['custTel']
                    code.save() 
                    temp = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=request.session['transactionID']))
                    agreeCode = AgreementConfirmationCode.objects.filter(Q(transactionID=str(request.session['transactionID']))).last().code 
                    sendSMS(str(request.session['custTel']), f'{request.session['paymentTerm']} Agreement. This item can only be collected by a person with this agreement code and the telephone number used for this transaction. By Mentioning the: {agreeCode} to the officer to confirm means you have agreed to the contract.')     
            else:
                pass
        return render(request, 'sales/confirmAgreementCode.html', {'opt': str(request.session['paymentTermShort'])}) 
        
        
    # execute savePayment function
    def executeSavePayment(request, opt):
        # get agree code
        agreeCode = request.POST.get('agreeCode')
        agree = AgreementConfirmationCode.objects.filter(Q(transactionID=str(request.session['transactionID']))).last()
        if not agree.code == agreeCode:
                messages.set_level(request, messages.INFO)
                messages.error(request, {'message': 'The agreement code entered is wrong. Please ask the customer to mention the agreement code which has been sent through SMS of the phonenumber provided ', 'title': 'Wrong Agreement code!'}, extra_tags='wrongAgreementCode')
                return render(request, 'sales/state.html') 
        transactionID = request.session['transactionID']
        name = request.session['custName']
        tel = request.session['custTel']
        payAmount = request.session['payAmount']
        today = str(dt.date.today())
        today = dt.datetime.strptime(today, "%Y-%m-%d")
        temp = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=transactionID)) 

        if not tel and not name:
            messages.set_level(request, messages.INFO)
            messages.error(request, {'message': 'Customer name and phonenumber is required. ', 'title': 'No customer details'}, extra_tags='cutomerNameAndTelIsRequired')
            return render(request, 'sales/state.html') 
        
        if opt == 'PP':
            nextPayDate = today + dt.timedelta(days=int(request.session['numberOfDays']))  
            agreement = PaymentAgreement()
            agreement.branchRef = loginSessions(request, 'branch')
            agreement.transactionID = str(request.session['transactionID'])
            agreement.paymentTerm = str(request.session['paymentTerm'])      
            agreement.numberDays = int(request.session['numberOfDays'])
            agreement.daysBeforeNextPayment = int(request.session['numberOfDays'])   
            agreement.paneltyRatePerBreach = float(request.session['panelty'])
            agreement.nextPaymentDate = nextPayDate
            agreement.nextPaymentAmount = float(temp.amountToPay) - float(payAmount)
            agreement.totalAmount = temp.amountToPay
            agreement.save()

            agreeDetails = PaymentAgreementDetails()
            agreeDetails.payAgreemtRef = agreement
            agreeDetails.dateToPay = agreement.nextPaymentDate
            agreeDetails.paidOn = dt.datetime.now()
            agreeDetails.panelty = 0.00
            agreeDetails.amountPaid = payAmount
            agreeDetails.amountRemain = float(temp.amountToPay) - float(payAmount)
            agreeDetails.save()                    
            Payment.savePayment(request, transactionID, agreement.paymentTerm, payAmount, name, tel)

        elif opt == 'IA':
            nextPayDate = today + dt.timedelta(days=int(request.session['numberOfDays']))  
            agreement = PaymentAgreement()
            agreement.branchRef = loginSessions(request, 'branch')
            agreement.transactionID = str(request.session['transactionID'])
            agreement.paymentTerm = str(request.session['paymentTerm'])      
            agreement.numberDays = int(request.session['numberOfDays'])
            agreement.daysBeforeNextPayment = int(request.session['numberOfDays'])   
            agreement.paneltyRatePerBreach = float(request.session['panelty'])
            agreement.nextPaymentDate = nextPayDate
            agreement.nextPaymentAmount = float(request.session['amountPerPeriod'])
            agreement.totalAmount = temp.amountToPay
            agreement.save()

            agreeDetails = PaymentAgreementDetails()
            agreeDetails.payAgreemtRef = agreement
            agreeDetails.dateToPay = agreement.nextPaymentDate
            agreeDetails.paidOn = dt.datetime.now()
            agreeDetails.panelty = 0.00
            agreeDetails.amountPaid = 0
            agreeDetails.amountRemain = float(temp.amountToPay)
            agreeDetails.save()  

            #create payments dates
            n = 0
            today = str(dt.date.today())
            today = dt.datetime.strptime(today, "%Y-%m-%d")
            d = 0
            while n < int(request.session['numberOfPeriod']):
                if str(request.session['period']) == 'Daily':
                    d = 1
                elif str(request.session['period']) == 'Weekly':
                    d = 7
                elif str(request.session['period']) == 'Monthly':
                    d = 30
                elif str(request.session['period']) == 'Yearly':
                    d = 365

                payDate = today + dt.timedelta(days=d)
                
                # check is days are excluded                
                excludeDays = ExcludeDays.objects.filter(Q(transactionID=str(request.session['transactionID'])))
                if excludeDays.exists():
                    for exDay in excludeDays:
                        if exDay.days == str(payDate.strftime("%A")):
                            d = d +1
                        payDate = today + dt.timedelta(days=d)
                dat = DatesForPayments()
                dat.payAgreemtRef = agreement
                dat.date = payDate
                dat.day = payDate.strftime("%A")
                dat.save()
                today = dt.datetime.date(payDate) 
                today = dt.datetime.strptime(str(today), "%Y-%m-%d")
                n = n + 1                                           
            Payment.savePayment(request, transactionID, agreement.paymentTerm, 0, name, tel)
       
        elif opt == 'AP':
            with atomic():
                agreement = PaymentAgreement()
                agreement.branchRef = loginSessions(request, 'branch')
                agreement.transactionID = str(request.session['transactionID'])
                agreement.paymentTerm = str(request.session['paymentTerm'])      
                agreement.numberDays = 0
                agreement.daysBeforeNextPayment = 0 
                agreement.paneltyRatePerBreach = 0
                agreement.nextPaymentDate = dt.datetime.now()
                agreement.nextPaymentAmount = float(temp.amountToPay) - float(payAmount)
                agreement.totalAmount = temp.amountToPay
                agreement.save()

                agreeDetails = PaymentAgreementDetails()
                agreeDetails.payAgreemtRef = agreement
                agreeDetails.dateToPay = agreement.nextPaymentDate
                agreeDetails.paidOn = dt.datetime.now()
                agreeDetails.panelty = 0.00
                agreeDetails.amountPaid = payAmount
                agreeDetails.amountRemain = float(temp.amountToPay) - float(payAmount)
                agreeDetails.save()
                Payment.savePayment(request, transactionID, agreement.paymentTerm, payAmount, name, tel)

        # delete agreement code and clear all the used sessions
        agree.delete()
        request.session['paymentTerm'] = ''
        request.session['transactionID'] = ''
        request.session['custName'] = ''
        request.session['custTel'] = ''
        request.session['payAmount'] = ''        
        return redirect('salesSelling')
    
    #delete old code and generate new agreement code
    def deleteCurrentAgreementCode(request):
        agreeCode = AgreementConfirmationCode.objects.filter(Q(transactionID=str(request.session['transactionID'])))
        for c in agreeCode:
            c.delete()       
        return redirect('salesMakePayment')
        #return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    # save payment
    def savePayment(request, transactionID, paymentTerm, amountPaid, customerName, customerTel):
        temp = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=transactionID))            
        carts = AddToCart.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & 
                                        Q(transactionBy=loginSessions(request, 'user')) &
                                        Q(transactionID=transactionID))
        cash = float(amountPaid)
        with atomic():
            # save transaction records
            sales = SalesRecords()
            sales.branchRef = loginSessions(request, 'branch')
            sales.transactionID = transactionID
            sales.totalAmount = temp.totalPrice
            sales.discount = temp.discount
            paymentTerm = str(request.session['paymentTerm'])

            # save customers payment records
            payRecord = CustomerPayments()
            payRecord.transactionID = transactionID
            payRecord.date = dt.datetime.now()        

            #this part is base on payment terms
            if paymentTerm == 'Part payment (PP)':
                sales.amountToPay = temp.amountToPay
                sales.amountPaid = cash
                sales.amountOwe = float(sales.amountToPay) - cash                
                if float(sales.amountOwe) == 0:
                    sales.paymentTerms = 'Full payment (FP)'
                else:
                    sales.paymentTerms = 'Part payment (PP)'
            
            elif paymentTerm == 'Installment agreements (IA)':
                sales.amountToPay = temp.amountToPay
                sales.amountPaid = 0
                sales.amountOwe = float(sales.amountToPay) - float(sales.amountPaid)
                sales.paymentTerms = 'Installment agreements (IA)'
            
            elif paymentTerm == 'Advance payment (AP)':
                sales.amountToPay = temp.amountToPay
                sales.amountPaid = cash
                sales.amountOwe = float(sales.amountToPay) - cash
                sales.paymentTerms = 'Advance payment (AP)'
            
            else:
                sales.amountToPay = temp.amountToPay
                sales.amountPaid = temp.amountToPay
                sales.amountOwe = float(sales.amountToPay) - float(sales.amountPaid)
                if float(sales.amountOwe) == 0:
                    sales.paymentTerms = 'Full payment (FP)' 

            customerRef = RetailAndWholesaleCustomers.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(customerContact=customerTel))
            if customerRef.exists():
                customerRef = customerRef[0]
                sales.customerRef = customerRef           
            
            sales.transactionDate = dt.datetime.now()
            sales.customerName = customerName
            sales.customerTel = customerTel
            sales.transactionBy = loginSessions(request, 'user')
            sales.transactionIsConfirm = True
            sales.save()

            # keep customer owing records
            if sales.amountOwe > 0:
                Customers.customerOwe(request, transactionID, customerTel, 'Owed', float(round(float(sales.amountOwe),2)))

            checkCustomer = SalesRecords.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(customerRef__customerContact=customerTel)).order_by('-id')            
            # store all customer transactions
            if checkCustomer.exists():
                totalOwe = checkCustomer.aggregate(Sum('amountOwe'))['amountOwe__sum']
                #sales.customerOwingBalance = float(getLastOwingBalanace) + float(round(float(sales.amountOwe),2)).                            
                customerTransactions = AllCustomerTransactions()
                customerTransactions.customerRef = checkCustomer[0].customerRef
                customerTransactions.transactionID = transactionID
                customerTransactions.paymentTerms = sales.paymentTerms
                customerTransactions.transactionType = "Purchased"
                customerTransactions.transactionDate = dt.datetime.now()
                customerTransactions.transactionBy = loginSessions(request, 'user')
                customerTransactions.totalPrice = sales.totalAmount
                customerTransactions.discount = sales.discount
                customerTransactions.amountTopay = sales.amountToPay
                customerTransactions.currentPayment = cash
                customerTransactions.amountPaid = sales.amountPaid
                customerTransactions.amountOwe = sales.amountOwe
                customerTransactions.oweBalance = totalOwe
                customerTransactions.narration = f"Purchased items with payment term: {sales.paymentTerms}"
                customerTransactions.save()

            payRecord.salesRef = sales
            payRecord.amountPaid = sales.amountPaid
            payRecord.amountOwe = sales.amountOwe 
            payRecord.balance = float(sales.amountToPay) - float(sales.amountPaid)
            payRecord.paymentBy = loginSessions(request, 'user')
            payRecord.paidBy = f"{customerName} ({customerTel})"
            payRecord.save()

            # add cash to cash on hand
            cash = CashOnhand.objects.filter(Q(userRef=loginSessions(request, 'user')))
            if cash.exists():
                cash = cash[0]
            else:
                cash = CashOnhand()
                cash.branchRef = loginSessions(request, 'branch')
                cash.userRef = loginSessions(request, 'user')
                cash.date = dt.datetime.now()
                cash.save()
            cash.cash += float(sales.amountPaid)
            cash.totalTransaction += 1
            cash.save()

            # add cash to staff account
            accountTransactions(request, loginSessions(request, 'user').userID, 'Credit', float(sales.amountPaid), f'Payment for transaction with ID: {transactionID}')               
                
            # save customer items in this transaction
            for cart in carts:
                item = CustomerItemsPurchased()
                item.branchRef = cart.branchRef
                item.transactionID = cart.transactionID
                item.productName = cart.productRef.productName
                item.productCode = cart.productRef.productCode
                item.measureUnit = cart.productRef.retailAndWholesaleRef.measureRef.soldUnit
                item.quantity = cart.quantity
                item.pricePerUnit = cart.pricePerItem
                item.costPerUnit = cart.productRef.retailAndWholesaleRef.currentCostPriceRef.unitCostPrice
                item.discount = cart.discount
                item.unitDiscount = round(float(item.discount)/float(item.quantity), 2)
                item.totalPrice = cart.totalPrice
                item.save()

                product = Product.objects.get(Q(id=cart.productRef.id))

                #Note: if payment term is Advance Payment, don't deduct item bought from stock because the customer is not collecting the item yet                               
                if paymentTerm == 'Advance payment (AP)':
                    # store the customer item inside the AdvancePaymentItems table
                    payAgreement = PaymentAgreement.objects.get(Q(transactionID=str(request.session['transactionID'])))
                    advance = AdvancePaymentItems()
                    advance.branchRef = loginSessions(request, 'branch')
                    advance.customerRef = checkCustomer[0].customerRef
                    advance.productRef = product
                    advance.payAgreemtRef = payAgreement
                    advance.quatity = cart.quantity
                    advance.pricePerUnit = cart.pricePerItem
                    advance.costPerUnit = product.retailAndWholesaleRef.currentCostPriceRef.unitCostPrice
                    advance.totalPrice = cart.totalPrice
                    advance.save()

                    adDetails = AdvancePaymentItemsDetails()
                    adDetails.advanceItemRef = advance
                    adDetails.operationType = "Added"
                    adDetails.quantity = cart.quantity
                    adDetails.balace = cart.quantity
                    adDetails.date = dt.datetime.now()
                    adDetails.receiverName = customerName
                    adDetails.receiverTel = customerTel
                    adDetails.save()
                else:
                    tally = RetailWholesalesTally()
                    # deduct the item bought from the stock available
                    if product.retailAndWholesaleRef.measureRef.stockedUnit == 'Piece' and product.retailAndWholesaleRef.measureRef.soldUnit == 'Piece' or product.retailAndWholesaleRef.measureRef.stockedUnit == product.retailAndWholesaleRef.measureRef.soldUnit:
                        product.retailAndWholesaleRef.quantityRef.packQty -= float(cart.quantity)
                        product.retailAndWholesaleRef.quantityRef.uintQty -= float(cart.quantity)
                        tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                        tally.uintBalance = tally.balance
                        tally.quantity = cart.quantity
                        tally.unitQuantity = cart.quantity
                    else:
                        product.retailAndWholesaleRef.quantityRef.uintQty = float(product.retailAndWholesaleRef.quantityRef.uintQty) - float(cart.quantity) 
                        product.retailAndWholesaleRef.quantityRef.packQty = int(float(product.retailAndWholesaleRef.quantityRef.uintQty) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                        tally.uintBalance = product.retailAndWholesaleRef.quantityRef.uintQty
                        tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                        tally.quantity = int(float(cart.quantity) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                        tally.unitQuantity = cart.quantity
                    tally.narration = 'Sold a quantity of ' + str(cart.quantity) + ' ' + product.retailAndWholesaleRef.measureRef.soldUnit
                    tally.transactionType = 'Bought(Out)' 

                    #product.retailAndWholesaleRef.save() 
                    product.retailAndWholesaleRef.quantityRef.save()       
                    tally.retailAndWholesaleRef = product.retailAndWholesaleRef
                    tally.quantity = cart.quantity            
                    tally.transactionBy = loginSessions(request, 'user')            
                    tally.date = dt.datetime.now()
                    tally.save()
                # delete item from cart after being stored in the CustomerItemsPurchased table
                cart.delete()

            # print receipt
            Receipts.printSalesReceipt(request, transactionID)

            # delete transaction ID from TransactionID table after the transaction
            transactionID = TransactionIDs.objects.get(Q(transactionID=transactionID))
            transactionID.delete()
            # delete the temporal purchase details after the transaction
            temp.delete()   

    # this is where the payment agreement is going to be save
    def savePayAgreement(request):
        return HttpResponse()
    
    # get the name of the customer when customer phonenumber is selected
    def getCustomerName(request):
        customerTel = request.POST.get('customerTel')
        print(customerTel)
        customerList = RetailAndWholesaleCustomers.objects.filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(customerContact=customerTel))
        customerName = ''
        if customerList.exists():
            customerName = customerList[0].customerName
        return JsonResponse({'data': customerName})


    # give discount to the customer by reducing the price of the item
    def discount(request):
        transactionID = request.POST.get('transactionID')
        amoutnOff = request.POST.get('amoutnOff')  
        with atomic():      
            temp = TemporalPurchaseDetails.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(transactionID=transactionID))           
            rate = (float(amoutnOff) / float(temp.totalPrice)) * 100
            temp.discountRate = float('%.2f' % rate)
            temp.amountToPay = float(temp.totalPrice) - float(amoutnOff)
            temp.discount = amoutnOff
            temp.save()
        return redirect('salesMakePayment')


#sales records, Repayments, To be collected items views
class SalesRecordsView(generic.View):
    def get(self, request):
        if not haveAccess(request, '10'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to sales records page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')  
        dashboardMenuAccess(request)
        sales = SalesRecords.objects.filter(Q(branchRef=loginSessions(request, 'branch'))).order_by('-id')
        return render(request, 'sales/salesRecords.html', {'transactions':sales })
    
    # Repayment of customer oweing amount
    def repayOwe(request):
        if not haveAccess(request, '15'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to repayment page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        repayments = SalesRecords.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(amountOwe__gt=0)).order_by('-id')
        return render(request, 'sales/repayment.html', {'transactions': repayments})

    # To be collected items under Advance payment term
    def toBeCollectedItems(request):
        if not haveAccess(request, '14'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to awaiting items (Advance payment) page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        advances = SalesRecords.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(paymentTerms='Advance payment (AP)') & Q(amountOwe=0)).order_by('-id')
        return render(request, 'sales/toBeCollectedItems.html', {'transactions': advances})

 
 # performance analysis
class PerformanceAnalysis(generic.View):
    def get(self, request):
        if not haveAccess(request, '8'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to performance analysis page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        dashboardMenuAccess(request)
        request.session.setdefault('performanceType', '')
        request.session.setdefault('performSubject', '')
        request.session.setdefault('performFromDate', '')
        request.session.setdefault('performToDate', '')

        performanceType = request.session['performanceType']
        subject = request.session['performSubject']
        fromDate = request.session['performFromDate']
        toDate = request.session['performToDate']
        result = None
        title = ''
        totalTarget = 0
        
        branch = BusinessBranch.objects.filter(Q(branchID=subject) & Q(busRef=loginSessions(request, 'business')))
        branchName=''
        branchID = ''
        if branch.exists():
            branch = branch[0]
            branchName = branch.branchName
            branchID = branch.branchID
        if performanceType == '101':
                title = f'Most profitable Products at {branchName} ({branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('productName').annotate(
                   profit = Sum(ExpressionWrapper( F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField())),
                   discount = Sum('discount'),
                   totaltQty=Sum('quantity'),
                   totalSoldPrice = Sum('totalPrice'),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-profit')
                totalTarget = result.aggregate(Sum('profit'))['profit__sum']
               
        elif performanceType == '104':
                title = f'Most Purchased Products at {branchName} ({branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('productName').annotate(
                   quantityPurchase = Sum(ExpressionWrapper(F('quantity'), output_field=FloatField())),
                   totalSoldPrice = Sum('totalPrice'),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-quantityPurchase') 
                totalTarget = result.aggregate(Sum('quantityPurchase'))['quantityPurchase__sum']

        elif performanceType == '115':
                title = f'Amount Owed at {branchName} ({branchID}) from {fromDate} to {toDate}'
                result = SalesRecords.objects.values('transactionDate').annotate(
                   owe = Sum(ExpressionWrapper(F('amountOwe'), output_field=FloatField())),
                   amountPaid=Sum(ExpressionWrapper(F('amountPaid'), output_field=FloatField())),
                   amountToPay=Sum(ExpressionWrapper(F('amountToPay'), output_field=FloatField()))                   
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(transactionDate__gte=fromDate) & Q(transactionDate__lte=toDate))).order_by('transactionDate')
                totalTarget = result.aggregate(Sum('owe'))['owe__sum']

        elif performanceType == '109':
                title = f'Expenses incurred at {branchName} ({branchID}) from {fromDate} to {toDate}'
                result = OperationExpenses.objects.values('dateIncurred').annotate(
                   expenses = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(dateIncurred__gte=fromDate) & Q(dateIncurred__lte=toDate))).order_by('dateIncurred')
                totalTarget = result.aggregate(Sum('expenses'))['expenses__sum']

        elif performanceType == '116':
                title = f'Profit made at {branchName} ({branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   profit= Sum(ExpressionWrapper(F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField())),
                   totaltQty=Sum('quantity'),
                   totalSoldPrice = Sum('totalPrice'),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('date')
                totalTarget = result.aggregate(Sum('profit'))['profit__sum']
        
        elif performanceType == '119':
                title = f'Revenue generated at {branchName} ({branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   revenue= Sum(ExpressionWrapper(F('totalPrice'), output_field=FloatField())),
                   totaltQty=Sum('quantity'),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('date')
                totalTarget = result.aggregate(Sum('revenue'))['revenue__sum']
        
        elif performanceType == '120':
                title = f'Transactions made at {branchName} ({branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   transactions= Count('branchRef__busRef__busID')
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('date')  
                totalTarget = result.aggregate(Sum('transactions'))['transactions__sum']

        if performanceType == '100':
                title = f'Most profitable Products: from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('productName').annotate(
                   profit = Sum(ExpressionWrapper( F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField())),
                   discount = Sum('discount'),
                   totaltQty=Sum('quantity'),
                   totalSoldPrice = Sum('totalPrice'),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-profit')
                totalTarget = result.aggregate(Sum('profit'))['profit__sum']

        elif performanceType == '103':
                title = f'Most Purchased Products: from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('productName').annotate(qty=Sum('quantity'),
                   quantityPurchase = Sum(ExpressionWrapper(F('quantity'), output_field=FloatField())),
                   totalSoldPrice = Sum('totalPrice'),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-quantityPurchase')    
                totalTarget = result.aggregate(Sum('quantityPurchase'))['quantityPurchase__sum']  

        elif performanceType == '105':
                title = f'Branches Performance base on Revenue from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   revenue= Sum(ExpressionWrapper(F('totalPrice'), output_field=FloatField())),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-revenue')  
                totalTarget = result.aggregate(Sum('revenue'))['revenue__sum']   

        elif performanceType == '106':
                title = f'Branches Performance base on profit from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   profit= Sum(ExpressionWrapper(F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField())),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField())),
                   totalSoldPrice = Sum('totalPrice'),
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-profit') 
                totalTarget = result.aggregate(Sum('profit'))['profit__sum']  


        elif performanceType == '107':
                title = f'Branches Performance base on transactions from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   transactions= Count('branchRef__branchID')
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-transactions')  
                totalTarget = result.aggregate(Sum('transactions'))['transactions__sum']

        elif performanceType == '108':
                title = f'Amount owe at each Branch from {fromDate} to {toDate}'
                result = SalesRecords.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   owe = Sum(ExpressionWrapper(F('amountOwe'), output_field=FloatField())),
                   amountPaid=Sum(ExpressionWrapper(F('amountPaid'), output_field=FloatField())),
                   amountToPay=Sum(ExpressionWrapper(F('amountToPay'), output_field=FloatField())) 
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(transactionDate__gte=fromDate) & Q(transactionDate__lte=toDate))).order_by('-owe') 
                totalTarget = result.aggregate(Sum('owe'))['owe__sum']

        elif performanceType == '110':
                title = f'Expenses at each branch from {fromDate} to {toDate}'
                result = OperationExpenses.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   expenses = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(dateIncurred__gte=fromDate) & Q(dateIncurred__lte=toDate))).order_by('-expenses') 
                totalTarget = result.aggregate(Sum('expenses'))['expenses__sum']

        elif performanceType == '111':
                title = f'Business Performance base on profit from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   profit= Sum(ExpressionWrapper(F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField())),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField())),
                   totalSoldPrice = Sum('totalPrice'),
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-profit')
                totalTarget = result.aggregate(Sum('profit'))['profit__sum']

        elif performanceType == '117':
                title = f'Business Performance base on Revenue from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   revenue= Sum(ExpressionWrapper(F('totalPrice'), output_field=FloatField())),
                   totalCost=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-revenue') 
                totalTarget = result.aggregate(Sum('revenue'))['revenue__sum']

        elif performanceType == '118':
                title = f'Business Performance base on Transactions from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   transactions= Count('branchRef__busRef__busID')
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-transactions') 
                totalTarget = result.aggregate(Sum('transactions'))['transactions__sum']

        elif performanceType == '112':
                title = f'Business Expenses incurred from {fromDate} to {toDate}'
                result = OperationExpenses.objects.values('dateIncurred').annotate(
                   expenses = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(dateIncurred__gte=fromDate) & Q(dateIncurred__lte=toDate))).order_by('-expenses')
                totalTarget = result.aggregate(Sum('expenses'))['expenses__sum'] 

        elif performanceType == '113':
                title = f'Cash Shortages made at each branch from {fromDate} to {toDate}'
                result = OversAndShortagesRecord.objects.values('oversAndShortagesRef__branchRef__branchName', 'oversAndShortagesRef__branchRef__branchID').annotate(
                   shortages = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(oversAndShortagesRef__branchRef__busRef=loginSessions(request, 'business')) & Q(transactionType='Shortage') & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-shortages') 
                totalTarget = result.aggregate(Sum('shortages'))['shortages__sum'] 

        elif performanceType == '114':
                title = f'Cash Overs made at each branch from {fromDate} to {toDate}'
                result = OversAndShortagesRecord.objects.values('oversAndShortagesRef__branchRef__branchName', 'oversAndShortagesRef__branchRef__branchID').annotate(
                   overs = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(oversAndShortagesRef__branchRef__busRef=loginSessions(request, 'business')) & Q(transactionType='Overs') & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-overs') 
                totalTarget = result.aggregate(Sum('overs'))['overs__sum']

        if request.user_agent.is_mobile:
            return render(request, 'sales/perfomanceAnalysisMobile.html', {'results': result, 'title': title, 'performanceType': performanceType, 'totalTarget': totalTarget})
        else:
            return render(request, 'sales/perfomanceAnalysis.html', {'results': result, 'title': title, 'performanceType': performanceType, 'totalTarget': totalTarget})
    

    def post(self, request):
        performanceType = request.POST.get('performanceType')
        subject = request.POST.get('subject')
        fromDate = request.POST.get('fromDate')
        toDate = request.POST.get('toDate')
        
        #store
        request.session['performanceType'] = performanceType
        if subject == None:
            request.session['performSubject'] = 'non'
        else:
            request.session['performSubject'] = subject        
        request.session['performFromDate'] = fromDate
        request.session['performToDate'] = toDate
        return redirect('perfomanceAnalysis')

    # get searching results
    def getSearchResult(request):
        performanceType = request.session['performanceType']
        subject = request.session['performSubject']
        fromDate = request.session['performFromDate']
        toDate = request.session['performToDate']
        
        x = []
        y = [] 
        title = ''
        result = None
        if subject != 'non':
            branch = BusinessBranch.objects.get(Q(branchID=subject) & Q(busRef=loginSessions(request, 'business')))
            if performanceType == '101':
                chartType = 'bar'
                title = f'Most profitable Products at {branch.branchName} ({branch.branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('productName').annotate(
                   profit = Sum(ExpressionWrapper( F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-profit')
                i = 0
                for d in result:
                    x.append(d['productName'])
                    y.append(d['profit'])
                    i += 1

            elif performanceType == '104':
                chartType = 'bar'
                title = f'Most Purchased Products at {branch.branchName} ({branch.branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('productName').annotate(
                   quantityPurchase = Sum(ExpressionWrapper(F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-quantityPurchase')
                i = 0
                for d in result:
                    x.append(d['productName'])
                    y.append(d['quantityPurchase'])
                    i += 1

            elif performanceType == '115':
                chartType = 'line'
                title = f'Amount Owed at {branch.branchName} ({branch.branchID}) from {fromDate} to {toDate}'
                result = SalesRecords.objects.values('transactionDate').annotate(
                   owe = Sum(ExpressionWrapper(F('amountOwe'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(transactionDate__gte=fromDate) & Q(transactionDate__lte=toDate))).order_by('transactionDate')           
                for d in result:
                    x.append(d['transactionDate'])
                    y.append(d['owe'])

            elif performanceType == '109':
                chartType = 'line'
                title = f'Expenses incurred at {branch.branchName} ({branch.branchID}) from {fromDate} to {toDate}'
                result = OperationExpenses.objects.values('dateIncurred').annotate(
                   expenses = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(dateIncurred__gte=fromDate) & Q(dateIncurred__lte=toDate))).order_by('dateIncurred')           
                for d in result:
                    x.append(d['dateIncurred'])
                    y.append(d['expenses'])
            
            elif performanceType == '116':
                chartType = 'line'
                title = f'Profit made at {branch.branchName} ({branch.branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   profit= Sum(ExpressionWrapper(F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('date')           
                for d in result:
                    x.append(d['date'])
                    y.append(d['profit'])

            elif performanceType == '119':
                chartType = 'line'
                title = f'Revenue generated at {branch.branchName} ({branch.branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   revenue= Sum(ExpressionWrapper(F('totalPrice'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('date')           
                for d in result:
                    x.append(d['date'])
                    y.append(d['revenue'])

            elif performanceType == '120':
                chartType = 'line'
                title = f'Transactions made at {branch.branchName} ({branch.branchID}) from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   transactions= Count('branchRef__busRef__busID')
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=subject) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('date')            
                for d in result:
                    x.append(d['date'])
                    y.append(d['transactions'])

        else:
            #Top most profitable Products
            if performanceType == '100':
                chartType = 'bar'
                title = f'Top most profitable Products from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('productName').annotate(
                   qty=Sum('quantity'),
                   profit = Sum(ExpressionWrapper( F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-profit')
                i = 0
                for d in result:
                    x.append(d['productName'])
                    y.append(d['profit'])
                    i += 1

            #Most Purchased Products
            elif performanceType == '103':
                chartType = 'bar'
                title = f'Most Purchased Products from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('productName').annotate(qty=Sum('quantity'),
                   quantityPurchase = Sum(ExpressionWrapper(F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-quantityPurchase')           
                for d in result:
                    x.append(d['productName'])
                    y.append(d['quantityPurchase'])

            elif performanceType == '105':
                chartType = 'bar'
                title = f'Branches Performance base on Revenue from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   revenue= Sum(ExpressionWrapper(F('totalPrice'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-revenue')           
                for d in result:
                    x.append(d['branchRef__branchName'])
                    y.append(d['revenue'])
            
            elif performanceType == '106':
                chartType = 'bar'
                title = f'Branches Performance base on profit from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   profit= Sum(ExpressionWrapper(F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-profit')           
                for d in result:
                    x.append(d['branchRef__branchName'])
                    y.append(d['profit'])

            elif performanceType == '107':
                chartType = 'bar'
                title = f'Branches Performance base on transactions from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   transactions= Count('branchRef__branchID')
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-transactions')        
                for d in result:
                    x.append(d['branchRef__branchName'])
                    y.append(d['transactions'])

            elif performanceType == '108':
                chartType = 'bar'
                title = f'Amount owe at each Branch from {fromDate} to {toDate}'
                result = SalesRecords.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   owe = Sum(ExpressionWrapper(F('amountOwe'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(transactionDate__gte=fromDate) & Q(transactionDate__lte=toDate))).order_by('-owe')           
                for d in result:
                    x.append(d['branchRef__branchName'])
                    y.append(d['owe'])

            elif performanceType == '110':
                chartType = 'bar'
                title = f'Expenses at each branch from {fromDate} to {toDate}'
                result = OperationExpenses.objects.values('branchRef__branchName', 'branchRef__branchID').annotate(
                   expenses = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(dateIncurred__gte=fromDate) & Q(dateIncurred__lte=toDate))).order_by('-expenses')           
                for d in result:
                    x.append(d['branchRef__branchName'])
                    y.append(d['expenses'])
            
            elif performanceType == '111':
                chartType = 'line'
                title = f'Business Performance base on profit from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   profit= Sum(ExpressionWrapper(F('totalPrice') - (F('costPerUnit') * F('quantity')), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-profit')           
                for d in result:
                    x.append(d['date'])
                    y.append(d['profit'])            

            elif performanceType == '117':
                chartType = 'line'
                title = f'Business Performance base on Revenue from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   revenue= Sum(ExpressionWrapper(F('totalPrice'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-revenue')           
                for d in result:
                    x.append(d['date'])
                    y.append(d['revenue'])

            elif performanceType == '118':
                chartType = 'line'
                title = f'Business Performance base on Transactions from {fromDate} to {toDate}'
                result = CustomerItemsPurchased.objects.values('date').annotate(
                   transactions= Count('branchRef__busRef__busID')
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-transactions')            
                for d in result:
                    x.append(d['date'])
                    y.append(d['transactions'])

            elif performanceType == '112':
                chartType = 'line'
                title = f'Business Expenses incurred from {fromDate} to {toDate}'
                result = OperationExpenses.objects.values('dateIncurred').annotate(
                   expenses = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(dateIncurred__gte=fromDate) & Q(dateIncurred__lte=toDate))).order_by('-expenses')           
                for d in result:
                    x.append(d['dateIncurred'])
                    y.append(d['expenses'])

            elif performanceType == '113':
                chartType = 'bar'
                title = f'Cash Shortages made at each branch from {fromDate} to {toDate}'
                result = OversAndShortagesRecord.objects.values('oversAndShortagesRef__branchRef__branchName', 'oversAndShortagesRef__branchRef__branchID').annotate(
                   shortages = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(oversAndShortagesRef__branchRef__busRef=loginSessions(request, 'business')) & Q(transactionType='Shortage') & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-shortages')           
                for d in result:
                    x.append(d['oversAndShortagesRef__branchRef__branchName'])
                    y.append(d['shortages'])

            elif performanceType == '114':
                chartType = 'bar'
                title = f'Cash Overs made at each branch from {fromDate} to {toDate}'
                result = OversAndShortagesRecord.objects.values('oversAndShortagesRef__branchRef__branchName', 'oversAndShortagesRef__branchRef__branchID').annotate(
                   overs = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(oversAndShortagesRef__branchRef__busRef=loginSessions(request, 'business')) & Q(transactionType='Overs') & (Q(date__gte=fromDate) & Q(date__lte=toDate))).order_by('-overs')           
                for d in result:
                    x.append(d['oversAndShortagesRef__branchRef__branchName'])
                    y.append(d['overs'])

        data = {'x': x, 'y': y, 'title': title, 'chartType': chartType}
        return JsonResponse({'data': data})    
    
    # filtering search parameters
    def search(request):
        option = request.POST.get('performanceType')
        data = None
        hideSelection2 = 'No'
        if option == '101' or option == '104' or option == '109' or option == '115' or option == '116' or option == '119' or option == '120':
            data = list(BusinessBranch.objects.values('branchName', 'branchID').filter(Q(busRef=loginSessions(request, 'business'))))
            hideSelection2 = 'No'
        else:
            hideSelection2 = 'Yes'
        return JsonResponse({'data': data, 'option': option, 'hideSelection2': hideSelection2})
    

# post payment and collection
class PostPaymentAndCollection(generic.View):
    def get(self, request, pk, opt):
        dashboardMenuAccess(request)
        transaction = SalesRecords.objects.get(Q(id=pk))
        items = CustomerItemsPurchased.objects.filter(Q(transactionID=transaction.transactionID))
        payments = CustomerPayments.objects.filter(Q(transactionID=transaction.transactionID)).order_by('-id')
        advanceItems = None
        agreement = None
        agreement = PaymentAgreement.objects.filter(Q(transactionID=transaction.transactionID))
        if agreement.exists():
            agreement =agreement.last()
            advanceItems = AdvancePaymentItems.objects.filter(Q(payAgreemtRef=agreement)).order_by('-id')        
        return render(request, 'sales/postPaymentAndCollection.html', {'opt': opt, 'items': items, 'transaction': transaction, 'payments': payments,'agreement': agreement, 'advanceItem': advanceItems})
    
    def post(self, request, pk, opt):
        transaction = SalesRecords.objects.get(Q(id=pk))
        if opt == 'payment':
            if not haveAccess(request, '15'):
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'You do not have access to repayment page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
                return render(request, 'user/state.html') 
            with atomic():
                amount = request.POST.get('amount')
                paidBy = request.POST.get('paidBy')
                sales = SalesRecords.objects.get(Q(id=pk))
                sales.amountPaid += float(amount)
                sales.amountOwe -= float(amount) 
                sales.save()
                
                checkCustomer = SalesRecords.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(customerRef__customerContact=sales.customerRef.customerContact)).order_by('-id')            
                # store all customer transactions
                if checkCustomer.exists():
                    totalOwe = checkCustomer.aggregate(Sum('amountOwe'))['amountOwe__sum']                           
                    customerTransactions = AllCustomerTransactions()
                    customerTransactions.customerRef = checkCustomer[0].customerRef
                    customerTransactions.transactionID = sales.transactionID
                    customerTransactions.paymentTerms = sales.paymentTerms
                    customerTransactions.transactionType = "Repayment"
                    customerTransactions.transactionDate = dt.datetime.now()
                    customerTransactions.transactionBy = loginSessions(request, 'user')
                    customerTransactions.totalPrice = sales.totalAmount
                    customerTransactions.discount = sales.discount
                    customerTransactions.amountTopay = sales.amountToPay
                    customerTransactions.currentPayment = amount
                    customerTransactions.amountPaid = sales.amountPaid
                    customerTransactions.amountOwe = sales.amountOwe
                    customerTransactions.oweBalance = totalOwe
                    customerTransactions.narration = f"Repayment for transaction with an ID: {sales.transactionID} and payment term: {sales.paymentTerms}"
                    customerTransactions.save()
                
                # keep customer oweing records
                Customers.customerOwe(request, sales.transactionID, sales.customerTel, 'Paid', float(round(float(amount), 2)))

                payment = CustomerPayments()
                payment.salesRef = sales
                payment.transactionID = sales.transactionID
                payment.amountPaid = float(amount)
                payment.balance = float(sales.amountOwe)
                payment.paidBy = paidBy
                payment.date = dt.datetime.now()
                payment.paymentBy = loginSessions(request, 'user')
                payment.save() 

                # add the cash to cash on hand
                cash = CashOnhand.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
                if cash.exists():
                    cash = cash[0]
                else:
                    cash = CashOnhand()
                    cash.branchRef = loginSessions(request, 'branch')
                    cash.userRef = loginSessions(request, 'user')
                    cash.date = dt.datetime.now()
                    cash.save()
                cash.cash += float(amount)
                cash.totalTransaction += 1
                cash.save()
                # receipt
                Receipts.repaymentReceipt(request, sales.transactionID, paidBy)
                # add cash to staff account
                accountTransactions(request, loginSessions(request, 'user').userID, 'Credit', float(amount), f'Payment for transaction with ID: {sales.transactionID}')  
        elif opt == 'collect':
            if not haveAccess(request, '14'):
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'You do not have access to awaiting collection page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
                return render(request, 'user/state.html') 
            with atomic():
                productRef = request.POST.get('productRef')
                qty = request.POST.get('qty')
                product = Product.objects.get(Q(id=productRef))

                """quantity = request.POST.get('quantity')
                additionalQuantity = request.POST.get('additionalQuantity')
                costPrice = request.POST.get('costPrice')
                unitCostPrice = request.POST.get('unitCostPrice')"""
                
                tally = RetailWholesalesTally()
                # deduct the item bought from the stock available
                if product.retailAndWholesaleRef.measureRef.stockedUnit == 'Piece' and product.retailAndWholesaleRef.measureRef.soldUnit == 'Piece' or product.retailAndWholesaleRef.measureRef.stockedUnit == product.retailAndWholesaleRef.measureRef.soldUnit:
                    product.retailAndWholesaleRef.quantityRef.packQty -= float(qty)
                    product.retailAndWholesaleRef.quantityRef.uintQty -= float(qty)
                    tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                    tally.uintBalance = tally.balance
                    tally.quantity = qty
                    tally.unitQuantity = qty
                else:
                    product.retailAndWholesaleRef.quantityRef.uintQty = float(product.retailAndWholesaleRef.quantityRef.uintQty) - float(qty) 
                    product.retailAndWholesaleRef.quantityRef.packQty = int(float(product.retailAndWholesaleRef.quantityRef.uintQty) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                    tally.uintBalance = product.retailAndWholesaleRef.quantityRef.uintQty
                    tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                    tally.quantity = int(float(qty) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                    tally.unitQuantity = qty
                tally.narration = f'{qty} {product.retailAndWholesaleRef.measureRef.soldUnit} of Advance payment items was/were collected'
                tally.transactionType = 'Bought(Out)' 

                #product.retailAndWholesaleRef.save() 
                product.retailAndWholesaleRef.quantityRef.save()       
                tally.retailAndWholesaleRef = product.retailAndWholesaleRef
                tally.quantity = qty            
                tally.transactionBy = loginSessions(request, 'user')            
                tally.date = dt.datetime.now()
                tally.save()  

                advanceItem = AdvancePaymentItems.objects.get(Q(payAgreemtRef__transactionID=transaction.transactionID) & Q(productRef=product))
                advanceItem.quatity -= float(qty)
                advanceItem.save()

                advanceItemTally = AdvancePaymentItemsDetails()
                advanceItemTally.advanceItemRef = advanceItem
                advanceItemTally.operationType = 'Collected'
                advanceItemTally.quantity = float(qty)
                advanceItemTally.balace = advanceItem.quatity
                advanceItemTally.date = dt.datetime.now()
                advanceItemTally.receiverName = ''
                advanceItemTally.receiverName = ''
                advanceItemTally.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


# return customer products bought
class ReturnProduct(generic.View):
    def get(self, request, productCode, transID):
        sales = SalesRecords.objects.get(transactionID=transID)
        product = Product.objects.get(Q(productCode=productCode) & Q(busRef=loginSessions(request, 'business')))
        item = CustomerItemsPurchased.objects.get(Q(transactionID=sales.transactionID) & Q(productCode=product.productCode))
        return render(request, 'sales/returnProduct.html', {'product': product, 'sales': sales, 'item': item})
    
    def post(self, request, productCode, transID):
        quantity = float(request.POST.get('quantity'))
        reason = request.POST.get('reason')

        with atomic():
            sales = SalesRecords.objects.get(transactionID=transID)
            product = Product.objects.get(Q(productCode=productCode) & Q(busRef=loginSessions(request, 'business')))
            tally = RetailWholesalesTally()
            tally.retailAndWholesaleRef = product.retailAndWholesaleRef 
            #item = CustomerItemsPurchased.objects.get(Q(transactionID=transID) & Q(productRef__id=productRef))
            item = CustomerItemsPurchased.objects.get(Q(transactionID=sales.transactionID) & Q(productCode=product.productCode))
            if quantity > item.quantity:
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'Return quantity cannot be more than purchased quantity.', 'title': 'Return Error'}, extra_tags='returnError')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/')) 

            item.quantity -= quantity
            item.quantityReturned += quantity
            item.totalPrice = item.pricePerUnit * item.quantity
            item.save()

            # restock the returned item            
            if product.retailAndWholesaleRef.measureRef.stockedUnit == 'Piece' and product.retailAndWholesaleRef.measureRef.soldUnit == 'Piece' or product.retailAndWholesaleRef.measureRef.stockedUnit == product.retailAndWholesaleRef.measureRef.soldUnit:
                product.retailAndWholesaleRef.quantityRef.packQty += quantity
                product.retailAndWholesaleRef.quantityRef.uintQty += quantity

                tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                tally.uintBalance = tally.balance
                tally.quantity = quantity
                tally.unitQuantity = quantity
                tally.narration = f"Customer Returned Product(s) {quantity} {product.retailAndWholesaleRef.measureRef.stockedUnit}"
                activityLogs(request, loginSessions(request, 'user').userID, 'Returned Product', f'You accepted customer return product of {quantity}. product: {product.productName} ({product.productCode})')
            else:
                qty = (float(quantity) * float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))
                product.retailAndWholesaleRef.quantityRef.uintQty += qty 
                product.retailAndWholesaleRef.quantityRef.packQty = int(float(product.retailAndWholesaleRef.quantityRef.uintQty) / float(product.retailAndWholesaleRef.quantityRef.qtyPerPack))    

                tally.balance = product.retailAndWholesaleRef.quantityRef.packQty
                tally.uintBalance = product.retailAndWholesaleRef.quantityRef.uintQty
                tally.quantity = quantity
                tally.unitQuantity = qty
                tally.narration = f"Customer Returned Product(s) {quantity} {product.retailAndWholesaleRef.measureRef.stockedUnit}/{qty} {product.retailAndWholesaleRef.measureRef.soldUnit}"               
                activityLogs(request, loginSessions(request, 'user').userID, 'Returned Product', f'You accepted customer return product of {quantity}/{qty}. Product: {product.productName} ({product.productCode})')
            product.retailAndWholesaleRef.quantityRef.save()

            tally.transactionType = 'Returned'
            tally.transactionBy = loginSessions(request, 'user')            
            tally.date = dt.datetime.now()
            tally.save() 

            returnRecord = ReturnedProductsRecord()
            returnRecord.salesRef = sales
            returnRecord.productRef = product
            returnRecord.quantity = quantity
            returnRecord.pricePerUnit = item.pricePerUnit
            returnRecord.totalPrice = float(item.pricePerUnit) * float(quantity)
            returnRecord.reason = reason
            returnRecord.returnedBy = loginSessions(request, 'user')
            returnRecord.date = dt.datetime.now()
            returnRecord.save()

            amtToReturn = 0.00

            # calculate discount given and subtract it from the amount to be returned  
            discountAmount = round(float(item.unitDiscount) * float(quantity), 2)

            # amount to return to the customer
            amtToReturn = round((float(item.pricePerUnit) * float(quantity)) - float(discountAmount), 2)

            # total refund amount
            sales.amountReturned += amtToReturn

            # Case 1: Customer still owes (partial or no payment)
            if float(sales.amountToPay) > float(sales.amountPaid):
                # Refund larger than debt
                if amtToReturn >= float(sales.amountOwe):
                    sales.amountToPay = round(float(sales.amountToPay) - amtToReturn, 2)
                    amtToReturn = round(amtToReturn - float(sales.amountOwe), 2)
                    sales.amountOwe = 0.00
                    print('Refund covers debt, remainder to customer:', amtToReturn)
                else:
                    # Refund only reduces debt
                    sales.amountToPay = round(float(sales.amountToPay) - amtToReturn, 2)
                    sales.amountOwe = round(float(sales.amountOwe) - amtToReturn, 2)
                    amtToReturn = 0.00
                    print('Refund reduces debt, nothing to customer')

            # Case 2: Full payment made
            else:
                # Customer gets full refund
                sales.amountToPay = round(float(sales.amountToPay) - amtToReturn, 2)
                sales.amountPaid = round(float(sales.amountPaid) - amtToReturn, 2)
                sales.amountOwe = 0.00
                print('Full payment, refund to customer:', amtToReturn)
            sales.save()

            # update amount to return 
            checkReturnAmout = ReturnAmountToCustomer.objects.filter(Q(salesRef__transactionID=transID))
            if checkReturnAmout.exists():
                returnAmount = checkReturnAmout[0]
                returnAmount.amountToPay += float(amtToReturn)
                returnAmount.save()
                print('Executed ========================================================================================')
            else:
                returnAmount = ReturnAmountToCustomer()
                returnAmount.salesRef = sales
                returnAmount.amountToPay = float(amtToReturn)
                returnAmount.save()    
                print('Executed ========================================================================================')    
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    

# receipts
class Receipts(generic.View):
    def printCollectedItems(request, transactionID, opt):
        if opt == 'awaitCollect':
            Receipts.waitCollectReceipt(request, transactionID)
            return redirect('salesToBeCollectedItems')
        elif opt == 'salesRecord':
            Receipts.printSalesReceipt(request, transactionID)
            return redirect('salesSalesRecords')
        elif opt == 'currentTransaction':
            saleR = SalesRecords.objects.filter(Q(transactionBy=loginSessions(request, 'user'))).order_by('-id')
            if saleR.exists():
                saleR = saleR[0]
                transactionID =  saleR.transactionID
                Receipts.printSalesReceipt(request, transactionID)
            return redirect('salesSelling')


    # Helper function to print a table row
    def print_row(item, qty, price,printerType, width=32):
        p = printerType
        # Adjust alignment for columns: item(left), qty(center), price(right)
        # This is a simplified formatting approach
        row = "{:<17} {:^4} {:>9}".format(item, qty, price)
        p.text(row + "\n")

    # receipt for sales
    def printSalesReceipt(request, transactionID):
        checkPrinter = AssignPrinterToUser.objects.filter(Q(userRef=loginSessions(request, 'user')))
        if checkPrinter.exists():
            printerCheck = checkPrinter[0]
            printer = None
            if printerCheck.printerRef.printerType == 'USB':
                VENDOR_ID = printerCheck.printerRef.id1
                PRODUCT_ID = printerCheck.printerRef.id2
                #printer = Usb(VENDOR_ID, PRODUCT_ID, interface=0, out_ep=0x01, in_ep=0x82)
                printer = Dummy()

            elif printerCheck.printerRef.printerType == 'Network':
                IP_Address = printerCheck.printerRef.id1
                Port_number = printerCheck.printerRef.id2
                printer = Usb(IP_Address, Port_number)

            elif printerCheck.printerRef.printerType == 'LP':
                printer = LP(printer_name=printerCheck.printerRef.id1)

            elif printerCheck.printerRef.printerType == 'Serial':
                dFile = printerCheck.printerRef.id1
                baudrate = printerCheck.printerRef.id2
                printer = Serial(devfile=dFile, baudrate=baudrate)

            elif printerCheck.printerRef.printerType == 'Win32Raw':
                printer = Win32Raw(printer_name=printerCheck.printerRef.id1)
            
            # --- Receipt Layout ---
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text(f"{loginSessions(request, 'business').busName}\n")
            printer.set(align='center', width=1, height=1)
            printer.text(f"{loginSessions(request, 'branch').branchName} \n")
            printer.text(f"{loginSessions(request, 'branch').branchEmail} | {loginSessions(request, 'branch').branchTel} \n")
            printer.text("-" * 32 + "\n")  
                        
            printer.text(f"Trans ID: {transactionID} \n")          
            printer.text("-" * 32 + "\n")

            # Table Header
            Receipts.print_row('Item', 'Qty', 'Price', printer)
            printer.text("-" * 32 + "\n")

            # Table Items
            customerItems = CustomerItemsPurchased.objects.filter(Q(transactionID=transactionID))
            for item in customerItems:
                Receipts.print_row(str(item.productName), str(item.quantity), str(item.totalPrice), printer)

            sale = SalesRecords.objects.get(Q(transactionID=transactionID))
            printer.text("-" * 32 + "\n")
            printer.text("{:<10} {:>21}".format("Payment", f"{sale.paymentTerms}") + "\n")
            
            printer.text("-" * 32 + "\n")
            printer.text("{:<20} {:>11}".format("Total Price", f"GHc{sale.totalAmount}") + "\n")
            printer.text("{:<20} {:>11}".format("Discount", f"GHc{sale.discount}") + "\n")
            printer.text("{:<20} {:>11}".format("Amount Due", f"GHc{sale.amountToPay}") + "\n")
            printer.text("{:<20} {:>11}".format("Amount Paid", f"GHc{sale.amountPaid}") + "\n")
            printer.text("{:<20} {:>11}".format("Outstanding Balance", f"GHc{sale.amountOwe}") + "\n")
            printer.text("-" * 32 + "\n")

            if sale.paymentTerms == 'Part payment (PP)' or sale.paymentTerms == 'Installment agreements (IA)':
                term = PaymentAgreement.objects.get(Q(transactionID=transactionID))
                printer.set(align='center', bold=True, width=2, height=2)
                printer.text(f"Payment Agreement Terms\n")
                printer.set(align='center', width=1, height=1)
                printer.text(f"Total days for payment: {term.numberDays}\n")
                printer.text(f"Next Payment Date: {term.nextPaymentDate}\n")
                printer.text(f"Next Payment Amount: {term.nextPaymentAmount}\n")
                printer.text(f"Penalty for each paymet breach: {term.paneltyRatePerBreach} % \n")
                printer.text("-" * 32 + "\n")

            printer.text(f"Trans Date: {sale.transactionDate} \n")
            printer.text("-" * 32 + "\n")

            printer.text("Customer Name: \n")
            printer.text(f"{sale.customerName} \n")
            printer.text("-" * 32 + "\n")

            printer.text(f"\n By: {loginSessions(request, 'user').userRef.firstName} {loginSessions(request, 'user').userRef.surname} \n")
            printer.text("-" * 32 + "\n")
            printer.text("Thanks for doing business with us! \n")

            printer.text("-" * 32 + "\n")
            printer.text("\n Designed by RN360!\n")
            printer.text("\n https://www.rn360.net \n")

            # Cut (optional, visual representation in dummy)
            printer.cut()
            # Output the result from the dummy printer
            print(printer.output.decode('utf-8'))
        else:
            pass

    # repayment receipts
    def repaymentReceipt(request, transactionID, paidBy):
        checkPrinter = AssignPrinterToUser.objects.filter(Q(userRef=loginSessions(request, 'user')))
        if checkPrinter.exists():
            printerCheck = checkPrinter[0]
            printer = None
            if printerCheck.printerRef.printerType == 'USB':
                VENDOR_ID = printerCheck.printerRef.id1
                PRODUCT_ID = printerCheck.printerRef.id2
                #printer = Usb(VENDOR_ID, PRODUCT_ID, interface=0, out_ep=0x01, in_ep=0x82)
                printer = Dummy()

            elif printerCheck.printerRef.printerType == 'Network':
                IP_Address = printerCheck.printerRef.id1
                Port_number = printerCheck.printerRef.id2
                printer = Usb(IP_Address, Port_number)

            elif printerCheck.printerRef.printerType == 'LP':
                printer = LP(printer_name=printerCheck.printerRef.id1)

            elif printerCheck.printerRef.printerType == 'Serial':
                dFile = printerCheck.printerRef.id1
                baudrate = printerCheck.printerRef.id2
                printer = Serial(devfile=dFile, baudrate=baudrate)

            elif printerCheck.printerRef.printerType == 'Win32Raw':
                printer = Win32Raw(printer_name=printerCheck.printerRef.id1)
            
            # --- Receipt Layout ---
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text(f"{loginSessions(request, 'business').busName}\n")
            printer.set(align='center', width=1, height=1)
            printer.text(f"{loginSessions(request, 'branch').branchName} \n")
            printer.text(f"{loginSessions(request, 'branch').branchEmail} | {loginSessions(request, 'branch').branchTel} \n")
            printer.text("-" * 32 + "\n")  
                        
            printer.text(f"Trans ID: {transactionID} \n")          
            printer.text("-" * 32 + "\n")
            
            customerPayments = CustomerPayments.objects.filter(Q(transactionID=transactionID)).order_by('-id')
            if customerPayments.exists():
                customerPayments = customerPayments[0]

            sale = SalesRecords.objects.get(Q(transactionID=transactionID))

            printer.text("-" * 32 + "\n")
            printer.text("{:<10} {:>21}".format("Payment", f"{sale.paymentTerms}") + "\n")
            
            printer.text("-" * 32 + "\n")
            printer.text("{:<20} {:>11}".format("Total Price", f"GHc{sale.totalAmount}") + "\n")
            printer.text("{:<20} {:>11}".format("Discount", f"GHc{sale.discount}") + "\n")
            printer.text("{:<20} {:>11}".format("Amount Due", f"GHc{sale.amountToPay}") + "\n")
            printer.text("{:<20} {:>11}".format("Current Payment", f"GHc{customerPayments.amountPaid}") + "\n")
            printer.text("{:<20} {:>11}".format("Total Payment", f"GHc{sale.amountPaid}") + "\n")
            printer.text("{:<20} {:>11}".format("Outstanding Balance", f"GHc{sale.amountOwe}") + "\n")
            printer.text("-" * 32 + "\n")

            printer.text(f"Trans Date: {customerPayments.date} \n")
            printer.text("-" * 32 + "\n")

            printer.text("Cash Paid By: \n")
            printer.text(f"{paidBy} \n")
            
            printer.text("-" * 32 + "\n")

            printer.text("Cash Received By: \n")
            printer.text(f"{loginSessions(request, 'user').userRef.firstName} {loginSessions(request, 'user').userRef.surname} \n")
            printer.text("-" * 32 + "\n")
            printer.text("Thanks for doing business with us! \n")

            printer.text("-" * 32 + "\n")
            printer.text("\n Designed by RN360!\n")
            printer.text("\n https://www.rn360.net \n")

            # Cut (optional, visual representation in dummy)
            printer.cut()
            # Output the result from the dummy printer
            print(printer.output.decode('utf-8'))

    # waiting collection receipts
    def waitCollectReceipt(request, transactionID):
        checkPrinter = AssignPrinterToUser.objects.filter(Q(userRef=loginSessions(request, 'user')))
        if checkPrinter.exists():
            printerCheck = checkPrinter[0]
            printer = None
            if printerCheck.printerRef.printerType == 'USB':
                VENDOR_ID = printerCheck.printerRef.id1
                PRODUCT_ID = printerCheck.printerRef.id2
                #printer = Usb(VENDOR_ID, PRODUCT_ID, interface=0, out_ep=0x01, in_ep=0x82)
                printer = Dummy()

            elif printerCheck.printerRef.printerType == 'Network':
                IP_Address = printerCheck.printerRef.id1
                Port_number = printerCheck.printerRef.id2
                printer = Usb(IP_Address, Port_number)

            elif printerCheck.printerRef.printerType == 'LP':
                printer = LP(printer_name=printerCheck.printerRef.id1)

            elif printerCheck.printerRef.printerType == 'Serial':
                dFile = printerCheck.printerRef.id1
                baudrate = printerCheck.printerRef.id2
                printer = Serial(devfile=dFile, baudrate=baudrate)

            elif printerCheck.printerRef.printerType == 'Win32Raw':
                printer = Win32Raw(printer_name=printerCheck.printerRef.id1)
            
            # --- Receipt Layout ---
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text(f"{loginSessions(request, 'business').busName}\n")
            printer.set(align='center', width=1, height=1)
            printer.text(f"{loginSessions(request, 'branch').branchName} \n")
            printer.text(f"{loginSessions(request, 'branch').branchEmail} | {loginSessions(request, 'branch').branchTel} \n")
            printer.text("-" * 32 + "\n")  
                        
            printer.text(f"Trans ID: {transactionID} \n")          
            printer.text("-" * 32 + "\n")

            printer.text("Items Collection: \n")

            # Table Header
            Receipts.print_row('Item', 'Qty', 'Balance', printer)
            printer.text("-" * 32 + "\n")

            # Table Items
            customerItems = AdvancePaymentItemsDetails.objects.filter(Q(advanceItemRef__payAgreemtRef__transactionID=transactionID) & Q(date__date=dt.datetime.now())).order_by('-id')
            if customerItems.exists():
                for item in customerItems:
                    Receipts.print_row(str(item.advanceItemRef.productRef.productName), str(item.quantity), str(item.balace), printer)
                
                customerItems = customerItems[0]

                printer.text(f"Trans Date: {customerItems.date} \n")
                printer.text("-" * 32 + "\n")

                printer.text("Receiver Name: \n")
                printer.text(f"{customerItems.receiverName} \n")
                printer.text("-" * 32 + "\n")

                printer.text(f"\n By: {loginSessions(request, 'user').userRef.firstName} {loginSessions(request, 'user').userRef.surname} \n")
                printer.text("-" * 32 + "\n")
                printer.text("Thanks for doing business with us! \n")

                printer.text("-" * 32 + "\n")
                printer.text("\n Designed by RN360!\n")
                printer.text("\n https://www.rn360.net \n")
                # Cut (optional, visual representation in dummy)
                printer.cut()
                # Output the result from the dummy printer
                print(printer.output.decode('utf-8'))
        else:
            pass


# Refund 
class Refund(generic.View):
    def get(self, request):
        refunds = ReturnAmountToCustomer.objects.filter(Q(salesRef__branchRef=loginSessions(request, 'branch')) & Q(amountToPay__gt=0)).order_by('-id').order_by('status')
        return render(request, 'sales/refund.html', {'refunds': refunds})
    
    def post(self, request):
        return HttpResponse()
    

    # Refund the item returned by the customer
    def customerRefund(request, pk):
        refund = ReturnAmountToCustomer.objects.get(Q(id=pk))
        return render(request, 'sales/refundAmountToCustomer.html', {'refund': refund})
    
    def saveCustomerRefund(request, pk):
        passW = request.POST.get('confirm')
        with atomic():
            refund = ReturnAmountToCustomer.objects.get(Q(id=pk))
            if check_password(password=passW, encoded=loginSessions(request, 'user').password):
                
                cash = CashOnhand.objects.filter(Q(userRef=loginSessions(request, 'user')))
                if cash.exists():
                    cash = cash[0]
                    if float(cash.cash) >= float(refund.amountToPay):
                        refund.status = 'Refunded'
                        # debit amount from cash on hand
                        cash.cash -= float(refund.amountToPay)
                        cash.save()
                        # debit amount from users account
                        accountTransactions(request, loginSessions(request, 'user').userID, 'Debit', float(refund.amountToPay), f'Payment of refund with transaction ID: {refund.salesRef.transactionID}')  
                        refund.save()
                    else:
                        messages.set_level(request, messages.WARNING)
                        messages.warning(request, {'message': 'Cash on hand is less than refund amount.', 'title': 'Transaction Failed'}, extra_tags='cashOnHandIslessThanRefundAmount')
                        return render(request, 'sales/state.html', {'refund': refund})                
                return redirect('salesRefund')
            else:
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'You have entered wrong password.', 'title': 'Wrong Password'}, extra_tags='passwordNotCorrectForRefund')
                return render(request, 'sales/state.html', {'refund': refund})


