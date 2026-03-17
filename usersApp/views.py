from django.shortcuts import render, redirect
from django.views import generic
from usersApp.models import UserAccess, UserLogs, UserRef, Users
from django.http import HttpResponse, HttpResponseRedirect
from businessApp.models import BusinessBranch, BusinessAccess
from accountsApp.models import Accounts, CashDenominations
from loginAndOutApp import views as loginViews
from django.db.models import Sum, Q
from django.db import transaction
import datetime as dt
import random as rd
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from imageApp.views import ImageUpload
from imageApp.models import Images
from sms import sendSMS

# Create your views here.

def user(request):    
    if not haveAccess(request, '1'):
        messages.set_level(request, messages.WARNING)
        messages.warning(request, {'message': 'You do not have access to user management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
        return render(request, 'user/state.html')   
    loginViews.dashboardMenuAccess(request)
    user = UserRef.objects.get(Q(userID=str(request.session['userID'])))
    users = UserRef.objects.filter(Q(busRef__busRef__busID=str(request.session['busID'])))
    branch = BusinessBranch.objects.filter(Q(busRef__busID=user.busRef.busRef.busID)).order_by('branchName')

    access = {'100':haveAccess(request, '100'), '101':haveAccess(request, '101'), 
              '102':haveAccess(request, '102'), '103':haveAccess(request, '103')}
    
    pic = Images.objects.filter(Q(subjectID=request.session['userID']))
    picture = ''
    if pic.exists():
        picture = pic.order_by('-id')[0]
    return render(request, 'user/users.html', {'users': users, 'branch': branch, 'uAccess': access, 'picture': picture})


class NewUser(generic.View):
    def get(self, request):
        loginViews.dashboardMenuAccess(request)
        return render(request, 'user/newUser.html')

    def post(self, request):
        #user = UserRef.objects.get(Q(userID=str(request.session['userID'])))
        fName = request.POST.get('fName')
        lName = request.POST.get('lName')
        tel = request.POST.get('tel')
        email = request.POST.get('email')
        dob = request.POST.get('dob')
        town = request.POST.get('town')
        country= request.POST.get('country')
        branchID = request.POST.get('branch')
        qualification = request.POST.get('qualification')
        branch = BusinessBranch.objects.get(Q(branchID=branchID))
        newUserID = setNewUser(request, str(request.session['busID']), branch, fName, lName, dob, country, town, qualification, email, tel, False)
        uRef = UserRef.objects.get(Q(userID=newUserID))
        
        activityLogs(request, str(request.session['userID']), 'Added New User', 'Added new user with ID: '+ str(newUserID) + ' and '+ str(fName) + ' ' + str(lName))
        sendSMS(tel, 'Your User ID is: ' + str(uRef.userID) + ' and your temporary password is: ' + str(uRef.password) + '. Please change your password after logging in for the first time.')
        return redirect(to='user')
    

class EditUser(generic.View):
    def get(self, request, userID):
        loginViews.dashboardMenuAccess(request)
        if haveAccess(request, '101'):
            user = UserRef.objects.get(Q(userID=str(userID)))
            return render(request, 'user/editUser.html', {'user': user})
        else:
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to edit User Information.', 'title': 'Access Denied'}, extra_tags='noAccessToEditUser')
            return render(request, 'user/state.html')

    
    def post(self, request, userID):
        user = UserRef.objects.get(Q(userID=str(userID)))
        opt = request.POST.get('opt')

        if opt == 'names':
            fName = request.POST.get('fName')
            lName = request.POST.get('lName')
            user.userRef.firstName = fName
            user.userRef.surname = lName
            user.userRef.save()
            activityLogs(request, str(request.session['userID']), 'Changed User names', 'Changed the name of the user with an ID: '+ str(userID))
        elif opt == 'dob':
            dob = request.POST.get('dob')
            user.userRef.dob = dob
            user.userRef.save()
            activityLogs(request, str(request.session['userID']), 'Changed User DOB', 'Changed the date of birth of the user with an ID: '+ str(userID))
        elif opt == 'tel':
            tel = request.POST.get('tel')
            user.userRef.tel = tel
            user.userRef.save()
            activityLogs(request, str(request.session['userID']), 'Changed User Phone number', 'Changed the phone number of the user with an ID: '+ str(userID))
        elif opt == 'email':
            email = request.POST.get('email')
            user.userRef.email = email
            user.userRef.save()
            activityLogs(request, str(request.session['userID']), 'Changed User Email', 'Changed the email of the user with an ID: '+ str(userID))
        elif opt == 'country':
            country = request.POST.get('country')
            user.userRef.country = country
            user.userRef.save()
            activityLogs(request, str(request.session['userID']), 'Changed User country', 'Changed the country of the user with an ID: '+ str(userID))
        elif opt == 'town':
            town = request.POST.get('town')
            user.userRef.homeTown = town
            user.userRef.save()
            activityLogs(request, str(request.session['userID']), 'Changed User Home Town', 'Changed the home town of the user with an ID: '+ str(userID))
        elif opt == 'qualification':
            qualification = request.POST.get('qualification')
            user.userRef.qualification = qualification
            user.userRef.save()
            activityLogs(request, str(request.session['userID']), 'Changed User Qualification', 'Changed the qualification of the user with an ID: '+ str(userID))
        
        return HttpResponseRedirect('/users/edituser/'+ userID)



def setNewUser(request, busID, busRef, firstName, lastName, dob, country, homeTown, qualification, email, tel, userIsAdmin):
    uID = ''
    with transaction.atomic():
        userRefs = UserRef.objects.filter(Q(busRef__busRef__busID=busID))
        newUser = Users()
        newUser.firstName = firstName
        newUser.surname = lastName
        newUser.dob = str(dob)
        newUser.homeTown = homeTown
        newUser.country = country
        newUser.qualification = qualification
        newUser.email = email
        newUser.tel = tel
        newUser.date = dt.datetime.now()
        newUser.save()

        uRef = UserRef()
        uRef.userRef = newUser
        if userRefs.exists():
            nextID = userRefs.order_by('-id')[0]
            uRef.userID= str(int(nextID.userID) + 1)
            uID = str(int(nextID.userID) + 1)
            uRef.busRef = busRef
            uRef.password = str(rd.randrange(1000, 9999)) + '' + str(rd.randrange(10,99))
            uRef.passwordIsSet = False
        else:
            newID = str(busID) + '001'
            uRef.userID = newID
            uID = newID
            uRef.busRef = busRef
            uRef.password = str(rd.randrange(1000, 9999)) + '' + str(rd.randrange(10,99))
            uRef.passwordIsSet = False
        uRef.userIsAdmin = userIsAdmin
        uRef.save()

        # Create branch account for the user        
        account = Accounts()
        account.busRef = loginViews.loginSessions(request, 'business')
        account.branchRef = loginViews.loginSessions(request, 'branch')
        account.accountType = "Staff Account"
        account.accountName = str(firstName) + ' ' + str(lastName)
        account.accountBalance = 0.00 
        account.accountNumber = str(uRef.userID)
        account.save()
        # return user ID for future use
        sendSMS(tel, 'Your User ID is: ' + str(uRef.userID) + ' and your temporary password is: ' + str(uRef.password) + '. Please change your password after logging in for the first time.')
        return uID


class AccessAndRoles(generic.View):
    def get(self, request, userID):
        loginViews.dashboardMenuAccess(request)
        uAccess = {'100':haveAccess(request, '100'), '101':haveAccess(request, '101'),
              '102':haveAccess(request, '102'), '103':haveAccess(request, '103')}
        
        if haveAccess(request, '102') or haveAccess(request, '103'):
            user = UserRef.objects.get(Q(userID=str(userID)))
            admin = UserRef.objects.get(Q(userID=str(request.session['userID'])))
            branches = BusinessBranch.objects.filter(Q(busRef__busID=admin.busRef.busRef.busID))
            access = BusinessAccess.objects.all()
            userAccess = UserAccess.objects.filter(Q(userRef__userID=userID))
            
            # check access group
            checkGroup = {'1':False, '2':False, '3':False, '4':False, '5':False, '6':False}
            for uA in userAccess:
                if uA.accessRef.accessGroupCode == '1':
                    checkGroup['1'] = True
                if uA.accessRef.accessGroupCode == '2':
                    checkGroup['2'] = True
                if uA.accessRef.accessGroupCode == '3':
                    checkGroup['3'] = True
                if uA.accessRef.accessGroupCode == '4':
                    checkGroup['4'] = True
                if uA.accessRef.accessGroupCode == '5':
                    checkGroup['5'] = True
                if uA.accessRef.accessGroupCode == '6':
                    checkGroup['6'] = True

            hideRemoveButton = True
            if userAccess.count() < 5:
                hideRemoveButton = False
            return render(request, 'user/accessAndRole.html', {'user': user, 'branches': branches, 'access': access, 'uAccess': uAccess,
                                                           'userAccess': userAccess, 'hideRemoveButton': hideRemoveButton, 'checkGroup': checkGroup})
        else:
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to this page', 'title': 'Access Denied'}, 
                             extra_tags='roleAndAccessDenied')
            return render(request, 'user/state.html')

    def post(self, request, userID):
        user = UserRef.objects.get(Q(userID=userID))
        opt = request.POST.get('opt')

        with transaction.atomic():
            if opt == 'branch':
                branchCode = request.POST.get('currentBranch')
                branch = BusinessBranch.objects.get(Q(branchID=branchCode))

                # update user branch
                user = UserRef.objects.get(Q(userID=str(userID)))
                user.busRef = branch                
                user.save()
                
                # update accounts branch
                account = Accounts.objects.get(Q(accountNumber=str(userID)))
                account.branchRef = branch
                account.save()

            elif opt == 'accessLevel':
                accessLevel = request.POST.get('accessLevel')
                if accessLevel == 'Yes':
                    user.userIsAdmin = True
                elif accessLevel == 'No':
                    checkUsers = UserRef.objects.filter(~Q(userID=userID) & Q(userIsAdmin=True))
                    if checkUsers.exists():
                        user.userIsAdmin = False
                    else:
                        messages.set_level(request, messages.WARNING)
                        messages.warning(request, {'message': 'At list, one user shoud have an Administrator Access Level before you can change the Administrator Access Level Of this user to False', 
                                                   'title': 'Cannot change Administrator Access Level of this user!'}, extra_tags='cannotChangeAdminAccessOfThisUser')
                        return render(request, 'user/state.html')
                else:
                    pass
                user.save()
            elif opt == 'disableUser':
                disableUser = request.POST.get('disableUser')
                if user.userIsAdmin:
                    messages.set_level(request, messages.WARNING)
                    messages.warning(request, {'message': 'This user has an Administrator accessl Level. To disable this user, you have to first remove the user Administrator Access Level.',
                                               'title': 'You cannot Disable this User.'}, extra_tags='youCannotDisableThisUser')
                    return render(request, 'user/state.html')
                else:
                    setStatus(request, userID, disableUser)
            else:
                access = request.POST.getlist('access')
                for acc in access:
                    busAccess = BusinessAccess.objects.filter(Q(accessCode=acc))
                    for busA in busAccess:
                        if opt == 'add':
                            userAccess = UserAccess.objects.filter(Q(userRef__userID=userID) & Q(accessRef__accessCode=busA.accessCode))
                            if not userAccess.exists():
                                db = UserAccess()
                                db.accessRef = busA
                                db.userRef = user
                                db.save()
                        elif opt == 'remove':
                            db = UserAccess.objects.get(Q(userRef__userID=userID) & Q(accessRef__accessCode=busA.accessCode))
                            db.delete()
        return HttpResponseRedirect('/users/accessandrole'+ str(userID))


# check if user have access
def haveAccess(request, accessCode):
    uAccess = UserAccess.objects.filter(Q(userRef__userID=request.session['userID']) & Q(accessRef__accessCode=accessCode))
    user = UserRef.objects.get(Q(userID=request.session['userID']))
    found = False
    if uAccess.exists():
        found = True
    elif user.userIsAdmin:
        found = True
    return found


def setStatus(request, userID, status):
    user = UserRef.objects.get(Q(userID=str(userID)))
    user.status = status
    user.save()


def activityLogs(request, userID, title, details):
    user = UserRef.objects.get(Q(userID=userID))
    db = UserLogs()
    db.userRef = user
    db.logTitle = title
    db.logDetails = details
    db.date = dt.datetime.now()
    db.save()


def yourActivityLogs(request):
    loginViews.dashboardMenuAccess(request)
    activities = UserLogs.objects.filter(Q(userRef__userID=str(request.session['userID']))).order_by('-id')
    return render(request, 'user/activityLogs.html', {'activities': activities})


def profile(request):
    user = UserRef.objects.get(Q(userID=str(request.session['userID'])))
    uAccess = UserAccess.objects.filter(Q(userRef__userID=request.session['userID']))
    pic = Images.objects.filter(Q(subjectID=request.session['userID']))
    picture = ''
    if pic.exists():
        picture = pic.order_by('-id')[0]
    return render(request, 'user/profile.html', {'user': user, 'userAccess': uAccess, 'picture': picture})


class UploadProfileImage(generic.View):
    def get(self, request):
        loginViews.dashboardMenuAccess(request)
        return render(request, 'user/profilePicture.html')

    def post(self, request):
        file = request.FILES['upload']
        image = ImageUpload()
        image.upload(file, request.session['userID'])
        return redirect(to='profile')



