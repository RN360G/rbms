from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from usersApp.models import UserRef, UserAccess
from businessApp.models import BusinessBranch, Printers, AssignPrinterToUser
from django.db.models import Q, Sum, Count
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
    printers = Printers.objects.filter(Q(branchRef=loginSessions(request, 'branch')))
    checkPrinter = AssignPrinterToUser.objects.filter(Q(userRef=loginSessions(request, 'user')))
    if checkPrinter.exists():
        checkPrinter = checkPrinter[0]
    return render(request, 'dashboardApp/dashboard.html',{'access': access, 'picture': picture, 'printers': printers, 'assignedPrinter': checkPrinter})


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
    
    
