from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.db.models import Q, Sum
from businessApp.models import Business, BusinessBranch
import datetime as dt
from richnet360.models import ChargesType, Charges, Bill, BillPayments, CheckNextBillDate
from django.contrib import messages
from django.db import transaction
from usersApp.models import UserRef

# Create your views here.

class Richnet360(generic.View):
    def get(self, request):
        charges = {
            'Business Charge': 'Charges for running your business on RN360B', 
            'Branches Charge': 'Charges for each branch of your businesss',
            'Maintenance Charge': 'Charges for system maintenance',
            'SMS Charge': 'Charges for each SMS used',
            'Training and Customer Service': 'Charges for customer service and training',
            'Online Visibility Charge': 'Charges for branch or product online visibility',
            'Images Upload Charges': 'Charges for storing product images on RN360B' 
        }

        for charge, narration in charges.items():
            check = ChargesType.objects.filter(Q(product=charge))
            if not check.exists():
                db = ChargesType()
                db.product = charge
                db.narration = narration
                db.save()
            
        
        businesses = Business.objects.all()
        charges = ChargesType.objects.all().order_by('product')
        # bill businesses now
        BillBusiness.chargesBaseOnPeriod(self, request)
        return render(request, 'richnet360/businesses.html', {'businesses': businesses, 'charges': charges})
    
    def post(self, request):
        return HttpResponse()
    
    def addCharges(request):
        amount = request.POST.getlist('amount')
        period = request.POST.getlist('period')
        products = request.POST.getlist('product')
        
        with transaction.atomic():
            i = 0
            for product in products:  
                charge = ChargesType.objects.get(Q(product=product))                             
                charge.amount = amount[i]
                charge.period = period[i]
                charge.save()
                i = i + 1
                for business in Business.objects.filter(Q(status='Active')):
                    check = CheckNextBillDate.objects.filter(Q(busRef=business) & Q(chargeRef=charge))
                    if not check.exists():
                        check = CheckNextBillDate()
                        check.busRef = business
                        check.chargeRef = charge
                        if charge.period == 'Daily':
                             check.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=1)
                        elif charge.period == 'Weekly':
                             check.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=7)
                        elif charge.period == 'Monthly':   
                             check.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=30)
                        elif charge.period == 'Quarterly':
                             check.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=90)
                        elif charge.period == 'Semi-Annually':
                             check.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=180)
                        elif charge.period == 'Annually':
                             check.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=365)
                        else:                             
                            check.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=0) 
                        check.save()
                    else:
                        if check[0].nextBillDate == dt.datetime.now().date() and check[0].chargeRef.period != 'Per usage':
                            saveChages = Charges()
                            saveChages.busID = check[0].busRef
                            saveChages.product = check[0].chargeRef.product
                            saveChages.amount = check[0].chargeRef.amount
                            saveChages.date = dt.datetime.now()
                            saveChages.save()
                            
                            check[0].nextBillDate = dt.datetime.now().date() + dt.timedelta(days=30)
                            check[0].save()            
            return redirect('richnetDashboard')


    # registration number
    def registrationNumber(request):
        busID = request.POST.get('busID')
        opt = request.POST.get('opt')
        registerNumber = request.POST.get('registerNumber')
        with transaction.atomic():
            business = Business.objects.filter(Q(busID=busID))
            if business.exists():
                business = business[0]
                if opt == 'Confirm Registration':
                    business.registrationNumber = registerNumber
                    business.save()
                    return redirect('richnetDashboard')
                else:
                    if business.registrationNumber == registerNumber:
                        business.registrationNumber = None
                        business.save()
                        return redirect('richnetDashboard')
                    else:
                        messages.set_level(request, messages.WARNING)
                        messages.warning(request, {'message': f'You have entered wrong registration number', 'title': 'Wrong Registration Number'}, extra_tags='wrongRegistrationNumber')
                        return render(request, 'richnet360/state.html')
            else:
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': f'You have entered wrong business ID', 'title': 'Wrong Business ID'}, extra_tags='wrongBusinessID')
                return render(request, 'richnet360/state.html')     

    # change business status
    def changeStatus(request):
        with transaction.atomic():
            busID = request.POST.get('busID')
            opt = request.POST.get('opt')
            business = Business.objects.filter(Q(busID=busID))
            if business.exists():
                business = business[0]
                business.status = opt
                business.save()
                return redirect('richnetDashboard') 
            else:
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': f'You have entered wrong business ID', 'title': 'Wrong Business ID'}, extra_tags='wrongBusinessID')
                return render(request, 'richnet360/state.html')   

    def businessAdmin(request, pk):
        user = None
        business = Business.objects.get(Q(id=pk))
        branch = BusinessBranch.objects.filter(Q(busRef=business))
        if branch.exists():
            branch = branch[0]        
            user = UserRef.objects.filter(Q(busRef=branch))
            if user.exists():
                user = user[0]
        return render(request, 'richnet360/admin.html', {'user': user})     
    

# billing the business activities
class BillBusiness():
    # charges base on period
    def chargesBaseOnPeriod(self, request):
        with transaction.atomic():
            check = CheckNextBillDate.objects.filter(Q(nextBillDate__lte=dt.datetime.now().date()) & Q(chargeRef__period__in=['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Semi-Annually', 'Annually']))
            for dat in check:
                
                if dat.nextBillDate == dt.datetime.now().date() and dat.chargeRef.period == 'Daily':
                    # save charges of the business
                    saveChages = Charges()
                    saveChages.busID = dat.busRef
                    saveChages.product = dat.chargeRef.product
                    saveChages.amount = dat.chargeRef.amount
                    saveChages.date = dt.datetime.now()
                    saveChages.save()
                    # add charges to the current bill
                    dat.busRef.billRef.currentBill = dat.busRef.billRef.currentBill + dat.chargeRef.amount
                    dat.busRef.billRef.save()
                    # set next bill date
                    dat.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=1)
                    dat.save()
                
                if dat.nextBillDate == dt.datetime.now().date() and dat.chargeRef.period == 'Weekly':
                    # save charges of the business
                    saveChages = Charges()
                    saveChages.busID = dat.busRef
                    saveChages.product = dat.chargeRef.product
                    saveChages.amount = dat.chargeRef.amount
                    saveChages.date = dt.datetime.now()
                    saveChages.save()
                    # add charges to the current bill
                    dat.busRef.billRef.currentBill = dat.busRef.billRef.currentBill + dat.chargeRef.amount
                    dat.busRef.billRef.save()
                    # set next bill date
                    dat.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=1)
                    dat.save()

                if dat.nextBillDate == dt.datetime.now().date() and dat.chargeRef.period == 'Monthly':
                    # save charges of the business
                    saveChages = Charges()
                    saveChages.busID = dat.busRef
                    saveChages.product = dat.chargeRef.product
                    saveChages.amount = dat.chargeRef.amount
                    saveChages.date = dt.datetime.now()
                    saveChages.save()
                    # add charges to the current bill
                    dat.busRef.billRef.currentBill = dat.busRef.billRef.currentBill + dat.chargeRef.amount
                    dat.busRef.billRef.save()
                    # set next bill date
                    dat.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=1)
                    dat.save()
                
                if dat.nextBillDate == dt.datetime.now().date() and dat.chargeRef.period == 'Quarterly':
                    # save charges of the business
                    saveChages = Charges()
                    saveChages.busID = dat.busRef
                    saveChages.product = dat.chargeRef.product
                    saveChages.amount = dat.chargeRef.amount
                    saveChages.date = dt.datetime.now()
                    saveChages.save()
                    # add charges to the current bill
                    dat.busRef.billRef.currentBill = dat.busRef.billRef.currentBill + dat.chargeRef.amount
                    dat.busRef.billRef.save()
                    # set next bill date
                    dat.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=1)
                    dat.save()

                if dat.nextBillDate == dt.datetime.now().date() and dat.chargeRef.period == 'Semi-Annually':
                    # save charges of the business
                    saveChages = Charges()
                    saveChages.busID = dat.busRef
                    saveChages.product = dat.chargeRef.product
                    saveChages.amount = dat.chargeRef.amount
                    saveChages.date = dt.datetime.now()
                    saveChages.save()
                    # add charges to the current bill
                    dat.busRef.billRef.currentBill = dat.busRef.billRef.currentBill + dat.chargeRef.amount
                    dat.busRef.billRef.save()
                    # set next bill date
                    dat.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=1)
                    dat.save()
                
                if dat.nextBillDate == dt.datetime.now().date() and dat.chargeRef.period == 'Annually':
                    # save charges of the business
                    saveChages = Charges()
                    saveChages.busID = dat.busRef
                    saveChages.product = dat.chargeRef.product
                    saveChages.amount = dat.chargeRef.amount
                    saveChages.date = dt.datetime.now()
                    saveChages.save()
                    # add charges to the current bill
                    dat.busRef.billRef.currentBill = dat.busRef.billRef.currentBill + dat.chargeRef.amount
                    dat.busRef.billRef.save()
                    # set next bill date
                    dat.nextBillDate = dt.datetime.now().date() + dt.timedelta(days=1)
                    dat.save()

    
    #charges base on usage
    def chargesBaseOnUsage(self, request, busID, product):
        with transaction.atomic():
            check = CheckNextBillDate.objects.filter(Q(busRef__busID=busID) & Q(chargeRef__product=product) & Q(chargeRef__period='Per usage'))
            for dat in check:
                # save charges of the business
                saveChages = Charges()
                saveChages.busID = dat.busRef
                saveChages.product = dat.chargeRef.product
                saveChages.amount = dat.chargeRef.amount
                saveChages.date = dt.datetime.now()
                saveChages.save()
                # add charges to the current bill
                dat.busRef.billRef.currentBill = dat.busRef.billRef.currentBill + dat.chargeRef.amount
                dat.busRef.billRef.save()





