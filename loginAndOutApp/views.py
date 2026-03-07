from django.shortcuts import render, redirect
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from usersApp.models import UserRef
from businessApp.models import BusinessBranch, Business
from django.db.models import Sum, Q
from django.contrib import messages
from usersApp.views import setStatus, UserAccess
from imageApp.models import Images


# Create your views here.

class LogIn(generic.View):
    def get(self, request):
        return render(request, 'loginApp/login.html')

    def post(self, request):
        userID = request.POST.get('userID')
        passW = request.POST.get('passW')

        user = UserRef.objects.filter(Q(userID=userID)).order_by('-id')
        if user.exists():
            if user[0].status != 'Disabled':
                if check_password(password=passW, encoded=user[0].password) or (user[0].password == passW and not user[0].passwordIsSet):
                    # check if business status is active
                    if user[0].busRef.busRef.status == 'Active':
                        request.session['busName'] = str(user[0].busRef.busRef.busName)
                        request.session['busID'] = str(user[0].busRef.busRef.busID)
                        request.session['userID'] = str(user[0].userID)
                        request.session['userNames'] = str(user[0].userRef.firstName) + ' ' + str(user[0].userRef.surname)
                        request.session['branchID'] = str(user[0].busRef.branchID)
                        request.session['branchType'] = str(user[0].busRef.branchType)
                        request.session['branchName'] = str(user[0].busRef.branchName)
                        image = Images.objects.filter(Q(userRef=user[0]))
                        if image.exists():
                            image = image[0]
                            request.session['profileImage'] = image.image.url
                        #check user access and set session variables
                        dashboardMenuAccess(request)
                        setStatus(request, str(user[0].userID), 'Online')
                        if not user[0].passwordIsSet:
                            request.session['userID'] = str(user[0].userID)
                            return redirect(to='createPassword')
                        return redirect(to='dashboard')
                    elif user[0].busRef.busRef.status == 'Inactive':
                        messages.set_level(request, messages.WARNING)
                        messages.warning(request, {'message': 'This business account is inactive. please contact system administrator for help.', 'title': 'Business Account is blocked!'},
                                extra_tags='businessAccountIsClodeOrInactive')
                        return render(request, 'loginApp/state.html')
                    else:
                        messages.set_level(request, messages.WARNING)
                        messages.warning(request, {'message': 'This business account is closed by RN360B. Please contact system administarator for help.', 'title': 'Business is closed!'},
                                extra_tags='businessAccountIsClodeOrInactive')
                        return render(request, 'loginApp/state.html')

                else:
                    messages.set_level(request, messages.ERROR)
                    messages.error(request, {'message': 'Wrong User ID or Password.', 'title': 'Wrong User Credentials'},
                               extra_tags='loginCredentialsNotFound')
                    return render(request, 'loginApp/state.html')
            else:
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'Your access is disabled. Please contact your system administrator for further explaination!', 
                                           'title': 'Access Denied!'}, extra_tags='noLogInAccess')
                return render(request, 'loginApp/state.html')
        else:
              messages.set_level(request, messages.ERROR)
              messages.error(request, {'message': 'Wrong User ID or Password.', 'title': 'Wrong User Credentials'},
                               extra_tags='loginCredentialsNotFound')
              return render(request, 'loginApp/state.html')
        
    def loginOptions(request):
        return render(request, 'loginApp/loginOptions.html')
        

class RichNetLogin(generic.View):
    def get(self, request):
        return render(request, 'loginApp/richnetLogin.html')
    
    def post(self, request):
        userName = str(request.POST.get('userID'))
        passw = str(request.POST.get('passW'))
        try:
            user = User.objects.get(Q(username=userName))
            if check_password(password=passw, encoded=user.password):
                request.session['username'] = user.username
                request.session['fullName'] = user.get_full_name()
                return redirect('richnetDashboard')
            else:
                return render(request, 'richnet/state.html', {'state': 'itUserNotFound'})
        except User.DoesNotExist:
            messages.set_level(request, messages.ERROR)
            messages.error(request, {'message': 'Wrong User ID or Password.', 'title': 'Wrong User Credentials'}, extra_tags='richnetLoginCredentialsNotFound')
            return render(request, 'loginApp/state.html')


# customer login
class CustomerLogins(generic.View):
    def get(self, request):
        return render(request, 'loginApp/customerLogin.html')
    
    def post(self, request):
        return HttpResponse('')
    

# create customer account
class CreateCustomerAccount(generic.View):
    def get(self, request):
        return render(request, 'loginApp/createCustomerAcc.html')
    
    def post(self, request):
        
        return HttpResponse()
    

# generate new pin: use when the customer forget his pin
class GenerateNewPin(generic.View):
    def get(self, request):
        return render(request, 'loginApp/generateNewPin.html')
    
    def post(self, request):
        return HttpResponse()


class CreatePassword(generic.View):
    def get(self, request):
        return render(request, 'loginApp/createPassword.html')

    def post(self, request):
        user = UserRef.objects.get(Q(userID=str(request.session['userID'])))
        confirmPassW = request.POST.get('confirmPassW')
        passW = request.POST.get('passW')

        if len(str(passW)) >= 6:
            if str(passW)== str(confirmPassW):
                 user.password = make_password(password=passW)
                 user.passwordIsSet = True
                 user.save()
                 messages.set_level(request, messages.SUCCESS)
                 messages.success(request, {'message': 'You have successfuly created your password.', 'title': 'Password Creation is Successfuly', 'otherInfo': 'Please click the button below to log in to your account'},
                               extra_tags='passwordCreated')
            else:
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'Passwords do not match. Please try again.', 'title': 'Password Error'},
                               extra_tags='passwordCreationDontMatch')
        else:
            messages.set_level(request, messages.ERROR)
            messages.error(request, {'message': 'The Password should not be less than six(6) characters.', 'title': 'Password Error'},
                               extra_tags='passwordLessThenSixCharacters')
        return render(request, 'loginApp/state.html')
    

def logout(request, userID):
    del(request.session['busName'])
    del(request.session['busID'])
    del(request.session['userID'])
    del(request.session['userNames'])
    del(request.session['branchID'])
    del(request.session['branchName'])
    #del(request.session['branchType'])

    request.session['busName'] =''
    request.session['busID'] = ''
    request.session['userID'] = ''
    request.session['userNames'] = ''
    request.session['branchID'] = ''
    request.session['branchName'] = ''
    #request.session['branchType'] = ''
    setStatus(request, userID, 'Offline')
    
    # delete entire session
    request.session.flush()
    return redirect(to='login')


# logout RN360 Admin user
def logoutRN360Admin(request):
    del(request.session['username'])
    del(request.session['fullName'])
    request.session['username'] = ''
    request.session['fullName'] = ''
    return redirect('richnetLogin')




def loginSessions(request, sessionType):
    if sessionType == 'user':
        return UserRef.objects.get(Q(userID=request.session['userID']))
    elif sessionType == 'branch':
        return  BusinessBranch.objects.get(Q(branchID=str(request.session['branchID'])))  
    elif sessionType == 'business':
        return Business.objects.get(Q(busID=str(request.session['busID'])))
    

def dashboardMenuAccess(request):
    user = UserRef.objects.get(Q(userID=request.session['userID']))
    request.session['userManagement'] = False
    request.session['branchManagement'] = False
    request.session['warehouseManagement'] = False
    request.session['branchAccountManagement'] = False
    request.session['businessAccountManagement'] = False
    request.session['sellProducts'] = False
    request.session['cashAnalysis'] = False
    request.session['performanceAnalysis'] = False
    request.session['incomeStatement'] = False
    request.session['salesRecords'] = False
    request.session['customerRecords'] = False
    request.session['supplierRecords'] = False
    request.session['operationalExpenses'] = False
    request.session['awaitingCollection'] = False
    request.session['repayments'] = False
    request.session['refund'] = False
    userAccess = UserAccess.objects.filter(Q(userRef=user))

    if user.userIsAdmin:
        request.session['userManagement'] = True
        request.session['branchManagement'] = True
        request.session['warehouseManagement'] = True
        request.session['branchAccountManagement'] = True
        request.session['businessAccountManagement'] = True
        request.session['sellProducts'] = True
        request.session['cashAnalysis'] = True
        request.session['performanceAnalysis'] = True
        request.session['incomeStatement'] = True
        request.session['salesRecords'] = True
        request.session['customerRecords'] = True
        request.session['supplierRecords'] = True
        request.session['operationalExpenses'] = True
        request.session['awaitingCollection'] = True
        request.session['repayments'] = True
        request.session['refund'] = True
    else:
        for uA in userAccess:
            if uA.accessRef.accessCode == '1':
                request.session['userManagement'] = True
            if uA.accessRef.accessCode == '2':
                request.session['branchManagement'] = True
            if uA.accessRef.accessCode == '3':
                request.session['warehouseManagement'] = True
            if uA.accessRef.accessCode == '4':
                request.session['branchAccountManagement'] = True
            if uA.accessRef.accessCode == '5':
                request.session['businessAccountManagement'] = True
            if uA.accessRef.accessCode == '6':
                request.session['sellProducts'] = True
            if uA.accessRef.accessCode == '7':
                request.session['cashAnalysis'] = True
            if uA.accessRef.accessCode == '8':
                request.session['performanceAnalysis'] = True
            if uA.accessRef.accessCode == '9':
                request.session['incomeStatement'] = True
            if uA.accessRef.accessCode == '10':
                request.session['salesRecords'] = True
            if uA.accessRef.accessCode == '11':
                request.session['customerRecords'] = True
            if uA.accessRef.accessCode == '12':
                request.session['supplierRecords'] = True
            if uA.accessRef.accessCode == '13' :
                request.session['operationalExpenses'] = True
            if uA.accessRef.accessCode == '14':
                request.session['awaitingCollection'] = True
            if uA.accessRef.accessCode == '15':
                request.session['repayments'] = True
            if uA.accessRef.accessCode == '16':
                request.session['refund'] = True
        



