from django.shortcuts import render, redirect
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.hashers import check_password, make_password
from usersApp.models import UserRef
from businessApp.models import BusinessBranch, Business
from django.db.models import Sum, Q
from django.contrib import messages
from usersApp.views import setStatus


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
                    request.session['busName'] = str(user[0].busRef.busRef.busName)
                    request.session['busID'] = str(user[0].busRef.busRef.busID)
                    request.session['userID'] = str(user[0].userID)
                    request.session['userNames'] = str(user[0].userRef.firstName) + ' ' + str(user[0].userRef.surname)
                    request.session['branchID'] = str(user[0].busRef.branchID)
                    request.session['branchType'] = str(user[0].busRef.branchType)
                    request.session['branchName'] = str(user[0].busRef.branchName)
                    setStatus(request, str(user[0].userID), 'Online')
                    if not user[0].passwordIsSet:
                        request.session['userID'] = str(user[0].userID)
                        return redirect(to='createPassword')
                    return redirect(to='dashboard')
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



def loginSessions(request, sessionType):
    if sessionType == 'user':
        return UserRef.objects.get(Q(userID=request.session['userID']))
    elif sessionType == 'branch':
        return  BusinessBranch.objects.get(Q(branchID=str(request.session['branchID'])))  
    elif sessionType == 'business':
        return Business.objects.get(Q(busID=str(request.session['busID'])))
    
    

