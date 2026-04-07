from django.shortcuts import render, redirect
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Sum, Q, F
from marketPlaceApp.models import CustomerAddToCart, CustomerInfor
from loginAndOutApp.views import loginSessions, dashboardMenuAccess
from warehouseApp.models import Product
from salesApp.models import RetailWholesalesTally, SalesRecords, CustomerItemsPurchased
from accountsApp.models import OnlineAccounts
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from accountsApp.views import accountTransactions
from django.db.transaction import atomic
import random as rd
from usersApp.views import activityLogs, haveAccess
import datetime as dt

# Create your views here.
class OnlineOrderManager(generic.View):
    def get(self, request):
        if not haveAccess(request, '17'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to Online order management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 

        carts = (CustomerAddToCart.objects.filter(~Q(status='Received') & 
                                                  Q(branhRef=loginSessions(request, 'branch')) & ~Q(customerTel__isnull=True) & ~Q(customerTel='')                                                  
                                                  )                 
                 .values('branhRef__branchName', 'branhRef__busRef__busName', 'branhRef__branchID', 'status', 'customerTel', 'batchCode')
                 .annotate(totalPrice=Sum('totalPrice'), referenceCode = F('acceptedCode')))
        accounts = OnlineAccounts.objects.filter(Q(branchRef=loginSessions(request, 'branch')))
        return render(request, 'onlineOrder/orders.html', {'orders': carts, 'accounts': accounts})
    
    def post(self, request):
        return HttpResponse()
    
    # order items
    def customerOrderItems(request, tel, batchCode):
        if not haveAccess(request, '17'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to Online order management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        carts = CustomerAddToCart.objects.filter(Q(branhRef=loginSessions(request, 'branch')) & Q(customerTel=tel) & Q(batchCode=batchCode))
        return render(request, 'onlineOrder/customerOrderItems.html', {'orders': carts, 'batchCode': batchCode})
    
    # accept or reject payment request
    def confirmPaymentRequest(request):
        if not haveAccess(request, '17'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to Online order management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        with atomic():
            password = request.POST.get('password')
            batchCode = request.POST.get('batchCode')
            tel = request.POST.get('tel')
            status = request.POST.get('status')
            user = loginSessions(request, 'user')
            if not check_password(password=password, encoded=user.password):
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'Wrong Password. Please make sure the signed in portal has your name and user ID', 'title': 'Transaction failed'}, extra_tags='passwordNotFound')
                return render(request, 'onlineOrder/state.html')
            else:
                carts = CustomerAddToCart.objects.filter(Q(branhRef=loginSessions(request, 'branch')) & Q(customerTel=tel) & Q(batchCode=batchCode))
                acceptCode = f"RN{rd.randrange(1000,9999)}"
                for cart in carts:
                    if cart.status == 'Request Rejected':
                        cart.status = status
                        cart.acceptedCode = ''
                        cart.save()
                        activityLogs(request, loginSessions(request, 'user').userID, 'Rejected Payment Request', f'You rejected payment request with ID: {cart.batchCode}')
                    else:
                        cart.status = status
                        cart.acceptedCode = acceptCode
                        cart.save()
                        activityLogs(request, loginSessions(request, 'user').userID, 'Accepted Payment Request', f'You accepted payment request with ID: {cart.batchCode}')
                return redirect('onlineOrderManager')
    
    # confirm payment
    def confirmPayment(request):
        if not haveAccess(request, '17'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to Online order management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        with atomic():
            transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().second}{loginSessions(request, 'user').userID}{rd.randrange(1000, 9999)}" 
            password = request.POST.get('password')
            batchCode = request.POST.get('batchCode')
            tel = request.POST.get('tel')
            status = request.POST.get('status')
            paidTo = request.POST.get('paidTo')
            
            user = loginSessions(request, 'user')
            if not check_password(password=password, encoded=user.password):
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'Wrong Password. Please make sure the signed in portal has your name and user ID', 'title': 'Transaction failed'}, extra_tags='passwordNotFound')
                return render(request, 'onlineOrder/state.html')
            else:
                carts = CustomerAddToCart.objects.filter(Q(branhRef=loginSessions(request, 'branch')) & Q(customerTel=tel) & Q(batchCode=batchCode))
                if status == 'Payment Confirmed':                    
                    amount = 0.00
                    totalDiscount = 0.00
                    totalAmount = 0.00

                    referenceCode = f"RN{rd.randrange(1000,9999)}"
                    for cart in carts:
                        cart.status = status
                        cart.acceptedCode = referenceCode
                        cart.paidToAccount = paidTo
                        cart.save()

                        item = CustomerItemsPurchased()
                        item.branchRef = cart.branhRef
                        item.transactionID = transactionID
                        item.productName = cart.productRef.productName
                        item.productCode = cart.productRef.productCode
                        item.measureUnit = cart.productRef.retailAndWholesaleRef.measureRef.soldUnit
                        item.quantity = cart.quantity
                        item.pricePerUnit = cart.unitPrice
                        item.costPerUnit = cart.productRef.retailAndWholesaleRef.currentCostPriceRef.unitCostPrice
                        item.discount = cart.discount
                        item.unitDiscount = round(float(item.discount)/float(item.quantity), 2)
                        item.totalPrice = cart.totalPrice
                        item.save()

                        amount += float(cart.totalPrice)
                        totalDiscount += float(round(float(cart.discount), 2))

                        product = Product.objects.get(Q(id=cart.productRef.id))
                        totalAmount += float(round(float(product.retailAndWholesaleRef.currentCostPriceRef.unitSellingPrice) * float(cart.quantity), 2))
                    
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
                    
                    customer = CustomerInfor.objects.get(Q(tel=tel))
                    # save transaction records
                    sales = SalesRecords()
                    sales.branchRef = loginSessions(request, 'branch')
                    sales.transactionID = transactionID
                    sales.totalAmount = totalAmount
                    sales.discount = totalDiscount

                    sales.amountToPay = round(amount, 2)
                    sales.amountPaid = round(amount, 2)
                    sales.amountOwe = 0.00
                    sales.paymentTerms = 'Online Payment'


                    sales.transactionDate = dt.datetime.now()
                    sales.customerName = customer.customerName
                    sales.customerTel = tel
                    sales.transactionBy = loginSessions(request, 'user')
                    sales.transactionIsConfirm = True
                    sales.save()

                    # Credit the Paid to account
                    accountTransactions(request, paidTo, 'Credit', amount, f'Confirmed online payment with batch id: {batchCode} and an amount of {amount}')
                    activityLogs(request, loginSessions(request, 'user').userID, 'Confirmed Payment', f'You confirmed payment of the transaction with ID: {batchCode}')
                else:
                    activityLogs(request, loginSessions(request, 'user').userID, 'No payment', f'You confirmed no payment of the transaction with ID: {batchCode}')

                return redirect('onlineOrderManager')
            
    # reverse transaction
    def reverseTransaction(request):
        if not haveAccess(request, '17'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to Online order management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        with atomic():
            password = request.POST.get('password')
            batchCode = request.POST.get('batchCode')
            tel = request.POST.get('tel')
            user = loginSessions(request, 'user')
            if not check_password(password=password, encoded=user.password):
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'Wrong Password. Please make sure the signed in portal has your name and user ID', 'title': 'Transaction failed'}, extra_tags='passwordNotFound')
                return render(request, 'onlineOrder/state.html')
            else:
                carts = CustomerAddToCart.objects.filter(Q(branhRef=loginSessions(request, 'branch')) & Q(customerTel=tel) & Q(batchCode=batchCode))
                account = ''
                amount = 0.00
                for cart in carts:
                    cart.status = 'Waiting Payment Request'
                    cart.acceptedCode = ''
                    cart.save()
                    amount += float(cart.totalPrice)
                    account = cart.paidToAccount

                accountTransactions(request, account, 'Debit', amount, f'Reversed payment confirmation with batch code: {batchCode} and an amount of {amount}')
                activityLogs(request, loginSessions(request, 'user').userID, 'Reversed Online payment', f'You reversed online payment confirmation with batch code: {batchCode}')
                return redirect('onlineOrderManager')
            
    
    #package and deliver
    def packageAndDeliver(request, tel, batchCode):
        status = request.POST.get('status')
        password = request.POST.get('password')
        user = loginSessions(request, 'user')
        if check_password(password=password, encoded=user.password):
            carts = CustomerAddToCart.objects.filter(Q(branhRef=loginSessions(request, 'branch')) & Q(customerTel=tel) & Q(batchCode=batchCode))
            if status == 'Packaged':
                totalDiscount = 0.00


                for cart in carts:
                    cart.status = status
                    cart.save()
                    product = Product.objects.get(Q(id=cart.productRef.id))
                    if product.retailAndWholesaleRef.uintQty >= cart.quantity:
                        pass

            elif status == 'Delivered':
                cart.status = status
                cart.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'Wrong Password. Please make sure the signed in portal has your name and user ID', 'title': 'Transaction failed'}, extra_tags='passwordNotFound')
            return render(request, 'onlineOrder/state.html')  
           







