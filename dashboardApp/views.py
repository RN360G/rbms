from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import generic
from usersApp.models import UserAccess
from accountsApp.models import OversAndShortages
from salesApp.models import CashOnhand
from businessApp.models import Printers, AssignPrinterToUser
from django.db.models import Q
from imageApp.models import Images
from loginAndOutApp.views import dashboardMenuAccess, loginSessions

# Create your views here.

def dashboard(request):
    #groupAccess = UserAccess.objects.values('accessRef__accessGroupCode').filter(Q(userRef__userID=request.session['userID'])).annotate(Count('accessRef__accessGroupCode'))
    access = UserAccess.objects.filter(Q(userRef__userID=request.session['userID']))   
    
    pic = Images.objects.filter(Q(subjectID=request.session['userID']))
    picture = ''
    if pic.exists():
        picture = pic.order_by('-id')[0]
    dashboardMenuAccess(request)
    operaionTime = loginSessions(request, 'branch')
    oversShortage = OversAndShortages.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(fromAccountRef__accountNumber=loginSessions(request, 'user').userID))
    overs = 0.00
    shortage = 0.00
    if oversShortage.exists():
        overs = oversShortage[0].overAmount
        shortage = oversShortage[0].shortageAmount
    
    cashOnHand = CashOnhand.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
    cashOnH = 0.00
    totalTransactions = 0
    if cashOnHand.exists():
        cashOnH= cashOnHand[0].cash
        totalTransactions = cashOnHand[0].totalTransaction

    printers = Printers.objects.filter(Q(branchRef=loginSessions(request, 'branch')))
    checkPrinter = AssignPrinterToUser.objects.filter(Q(userRef=loginSessions(request, 'user')))
    if checkPrinter.exists():
        checkPrinter = checkPrinter[0]
    context = {
        'access': access, 
        'picture': picture, 
        'printers': printers, 
        'assignedPrinter': checkPrinter, 
        'operationTime': operaionTime,
        'cashOnHand': cashOnH,
        'overs': overs,
        'shortage': shortage,
        'totalTransactions': totalTransactions

    }
    return render(request, 'dashboardApp/dashboard.html', context)


class BuyCode(generic.View):
    def get(self, request):
        return render(request, 'dashboardApp/buyCode.html')

    def post(self, request):
        return HttpResponse()
    

def selectPrinter(request):
    printerID = request.POST.get('printer')
    printer = Printers(id=printerID)
    checkPrinter = AssignPrinterToUser.objects.filter(Q(userRef=loginSessions(request, 'user')))

    if checkPrinter.exists():
        checkPrinter = checkPrinter[0]
        checkPrinter.printerRef = printer
        checkPrinter.save()
    else:
        checkPrinter = AssignPrinterToUser()
        checkPrinter.printerRef = printer
        checkPrinter.userRef = loginSessions(request, 'user')
        checkPrinter.save()
    return redirect('dashboard')
    
    
