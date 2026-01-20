from django.db import models

# Create your models here.

class Users(models.Model):
    firstName = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    dob = models.DateField()
    country = models.CharField(max_length=50)
    homeTown = models.CharField(max_length=50)
    qualification = models.CharField(max_length=20, null=True)
    tel = models.CharField(max_length=20, null=True)
    email = models.EmailField(max_length=50, null=True)
    date = models.DateField()


class UserAccess(models.Model):
    accessRef = models.ForeignKey('businessApp.BusinessAccess', on_delete=models.CASCADE)
    userRef = models.ForeignKey('usersApp.UserRef', on_delete=models.CASCADE)


class UserLogs(models.Model):
    userRef = models.ForeignKey('usersApp.UserRef', on_delete=models.CASCADE, null=True)
    logDetails = models.CharField(max_length=200)
    logTitle = models.CharField(max_length=50, default='New activity log')
    date = models.DateTimeField()


class UserRef(models.Model):
    busRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    userRef = models.ForeignKey(Users, on_delete=models.CASCADE)
    userIsAdmin = models.BooleanField(default=False)
    accessRef = models.ForeignKey(UserAccess, on_delete=models.DO_NOTHING, null=True)
    logRef = models.ForeignKey(UserLogs, on_delete=models.DO_NOTHING, null=True)  # delete this later -----------------------
    userID = models.CharField(max_length=15) # This is the username
    password = models.CharField(max_length=260)
    status = models.CharField(max_length=10, default='Offline') # Online, Offline, Disabled
    passwordIsSet = models.BooleanField(default=False) # This is set to true if user is still using the default password


