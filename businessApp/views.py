from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from businessApp.models import Business, BusinessBranch, CodeBought, BusinessAccess
from accountsApp.models import Accounts
from loginAndOutApp.views import loginSessions
import datetime as dt
from django.db import transaction
from django.contrib import messages
from django.db.models import Sum, Q
from usersApp.models import UserRef
from businessApp.businessAccess import busAccess
from usersApp.views import activityLogs, setNewUser
from imageApp.models import Images
from django.contrib.auth.hashers import check_password
from celery import Celery


class AddBusiness(generic.View):
    def get(self, request):
        with transaction.atomic():
            for access in busAccess:
                bAccess = BusinessAccess.objects.filter(Q(accessCode=access))
                if bAccess.exists():
                    pass
                else:
                    db = BusinessAccess()
                    db.accessCode = access
                    db.accessTitle = busAccess[access][0]
                    db.accessDescription= busAccess[access][1]
                    db.accessGroupCode = busAccess[access][2]
                    db.date = dt.datetime.now()
                    db.save()
        return render(request, 'businessApp/addBuiness.html')

    def post(self, request):
        busType = request.POST.get('busType')
        busName = request.POST.get('busName')
        emial = request.POST.get('email')
        tel = request.POST.get('tel')
        fName = request.POST.get('fName')
        sName = request.POST.get('sName')
        dob = request.POST.get('dob')
        town = request.POST.get('town')
        qualification = request.POST.get('qualification')

        tel = str(tel)
        tel = tel[1:]
        tel = f'+233{tel}'

        with transaction.atomic():
            chkID = Business.objects.all().order_by('-id')
            nextID = 1000001
            if chkID.exists():
                a = chkID[0]
                nextID = int(a.busID) + 1
            bus = Business()
            bus.busID = nextID
            bus.busName = busName
            bus.busEmail = emial
            bus.busTel = tel
            bus.busOwner = str(fName) + ' ' + str(sName)
            bus.save()
            
            # busID session
            request.session['busID'] = str(bus.busID)

            # create business account
            account = Accounts()
            account.busRef = bus
            account.accountType = "Business Account"
            account.accountName = busName
            account.accountNumber = nextID
            account.save()

            # create branch
            busBranch = BusinessBranch()
            busBranch.busRef = bus
            busBranch.branchName = 'Head Branch'
            busBranch.branchID =  str(bus.busID) + '' + str('1')
            busBranch.branchEmail = emial
            busBranch.branchTel = tel
            busBranch.branchType = busType            
            busBranch.save()

            # set branchID session
            request.session['branchID'] = str(busBranch.branchID)

            # create branch account
            account = Accounts()
            account.busRef = bus
            account.branchRef = busBranch
            account.accountType = "Branch Account"
            account.accountName = busBranch.branchName
            account.accountNumber = busBranch.branchID
            account.save()
                    
            # session for the new user
            request.session['userID'] = str(nextID) + '001'
            setNewUser(request,nextID,busBranch, fName, sName, dob, '', town, qualification, emial, tel, True)
        messages.set_level(request, messages.INFO)
        messages.success(request, {'message': 'You have successfully created new Business Account.',
                              'title': 'New Business Account', 'credential': 'Check your SMS for your tamporal PASSWORD', 
                              'business': [busName, busType, emial, tel, str(bus.busOwner), bus.busID, busBranch.branchID]},
                               extra_tags='New Business')
        return render(request, 'businessApp/state.html')


class BusinessSettings(generic.View):
    user = None
    business = None

    def get(self, request):
        self.user = UserRef.objects.get(Q(userID=str(request.session['userID'])))
        self.branches = BusinessBranch.objects.filter(Q(busRef__busID=self.user.busRef.busRef.busID))
        owner = UserRef.objects.filter(Q(busRef__busRef__busID=str(request.session['busID']))).order_by("id")[0]
        self.lastBranchID = self.branches.order_by('-id')[0]
        self.business = Business.objects.get(Q(busID=self.user.busRef.busRef.busID))

        pic = Images.objects.filter(Q(subjectID=request.session['userID']))
        picture = ''
        if pic.exists():
            picture = pic.order_by('-id')[0]
        return render(request, 'businessApp/businessSettings.html', {'business': self.business, 'branches': self.branches, 'user': self.user, 'owner': owner, 'picture': picture})
    
    def post(self, request):
        branchName = request.POST.get('branchName')
        busType = request.POST.get('busType')
        email = request.POST.get('email')
        tel = request.POST.get('tel')

        self.user = UserRef.objects.get(Q(userID=str(request.session['userID'])))
        self.branches = BusinessBranch.objects.filter(Q(busRef__busID=self.user.busRef.busRef.busID))
        self.business = Business.objects.get(Q(busID=self.user.busRef.busRef.busID))

        lastID = BusinessBranch.objects.filter(Q(busRef__busID=self.user.busRef.busRef.busID)).order_by('-id')[0].branchID
        nextID = int(lastID) + 1

        with transaction.atomic():
            busBranch = BusinessBranch()
            busBranch.busRef = self.business
            busBranch.branchID = str(nextID)
            busBranch.branchTel = tel
            busBranch.branchEmail = email
            busBranch.branchType = busType
            busBranch.branchName = branchName
            busBranch.save()

            # create branch account
            account = Accounts()
            account.busRef = loginSessions(request, 'business')
            account.branchRef = busBranch
            account.accountType = "Branch Account"
            account.accountName = busBranch.branchName
            account.accountNumber = busBranch.branchID
            account.save()
            activityLogs(request, str(request.session['userID']), 'Created New Branch', 'Branch Name: '+ str(branchName) + '; Branch ID: '+ str(nextID))
        return redirect(to='businessSettings')
    

    def setWorkingHours(request, branchID, opt):
        user = UserRef.objects.get(Q(userID=str(request.session['userID'])))
        branch = BusinessBranch.objects.get(Q(branchID=branchID))
        if opt == 'render':
            return render(request, 'businessApp/workingHours.html', {'branch': branch})
        elif opt == 'process':
            opType = request.POST.get('opType')
            fromTime = request.POST.get('fromTime')
            toTime = request.POST.get('toTime')

            if opType == 'allTime':
                branch.operateAllTime = True
                branch.fromTime = None
                branch.toTime = None
                branch.save()
                activityLogs(request, str(request.session['userID']), 'Working hours Changed', 'Changed the working hours of '+ str(branch.branchName) +' (' + str(branch.branchID) + ') to all time')
            elif opType == 'specTime':
                branch.operateAllTime = False
                branch.fromTime = fromTime
                branch.toTime = toTime
                branch.save()
                activityLogs(request, str(request.session['userID']), 'Working hours Changed', 'Changed the working hours of: '+ str(branch.branchName) +' (' + str(branch.branchID) + ') from '+ str(fromTime) + ' to '+ str(toTime))
            else:
                pass
        else:
            pass
        return redirect(to='businessSettings')
    

    def onlineVisibility(request, branchID):
        branch = BusinessBranch.objects.get(Q(branchID=branchID))
        if branch.onlineVisibility:
            branch.onlineVisibility = False
            activityLogs(request, str(request.session['userID']), 'Online visibility changed', 'Changed online visibility to Offline')
        else:
            branch.onlineVisibility = True
            activityLogs(request, str(request.session['userID']), 'Online visibility changed', 'Changed online visibility to Online')
        branch.save()
        return redirect(to='businessSettings')


    def switchBranch(request):
        branchID = request.POST.get('branch')
        password = request.POST.get('Password')
        branch = None
        user = UserRef.objects.filter(Q(userID=str(request.session['userID'])))
        if user.exists():
            if check_password(password=password, encoded=user[0].password):
                branch = BusinessBranch.objects.get(Q(branchID=branchID))
                request.session['branchID'] = str(branch.branchID)
                request.session['branchName'] = str(branch.branchName)
                request.session['branchType'] = str(branch.branchType)
                activityLogs(request, str(request.session['userID']), 'Switched Branch', 'Switched to branch: '+ str(branch.branchName) + ' (' + str(branch.branchID) + ')')
                return redirect(to='dashboard')
            else:
                branch = BusinessBranch.objects.get(Q(branchID=branchID))
                messages.set_level(request, messages.INFO)
                messages.error(request, {'message': 'You have entered wrong password', 'title': 'Wrong Password'}, extra_tags='wrongPasswordSwitchBranch')
                activityLogs(request, str(request.session['userID']), 'Switched Branch', 'Failed to switch to branch: '+ str(branch.branchName) + ' (' + str(branch.branchID) + ')')
                return render(request, 'businessApp/state.html')
        else:
            return redirect(to='logIn')





