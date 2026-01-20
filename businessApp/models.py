from django.db import models

# Create your models here.

class Business(models.Model):
    busID = models.CharField(max_length=15)
    busName = models.CharField(max_length=50)
    busTel = models.CharField(max_length=20)
    busEmail = models.CharField(max_length=50)
    busOwner = models.CharField(max_length=50)
    registrationNumber = models.CharField(max_length=100, null=True) # this part wll be entered and verified by RN360 only    


class BusinessBranch(models.Model):
    busRef = models.ForeignKey('Business', on_delete=models.CASCADE)
    branchID = models.CharField(max_length=15)
    branchName = models.CharField(max_length=50)
    branchTel = models.CharField(max_length=20)
    branchEmail = models.CharField(max_length=50)
    branchType = models.CharField(max_length=15)  # Manufacturer, Distributor, Hotel, Resturant & Bar, Farm, etc
    operateAllTime = models.BooleanField(default=True)
    fromTime = models.TimeField(null=True)
    toTime = models.TimeField(null=True)
    onlineVisibility = models.BooleanField(default=False)
    branchAddress = models.CharField(max_length=100, null=True)


class CodeBought(models.Model):
    momoNumber = models.CharField(max_length=20)
    pin = models.CharField(max_length=4)
    date = models.DateField()


class BusinessAccess(models.Model):
    accessTitle = models.CharField(max_length=50)
    accessDescription = models.CharField(max_length=50)
    accessCode = models.CharField(max_length=6)
    accessGroupCode = models.CharField(max_length=2)    
    thisAccessIsPayable = models.BooleanField(default=False)
    date = models.DateField()
