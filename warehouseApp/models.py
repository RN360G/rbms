from django.db import models
from businessApp.models import Business, BusinessBranch
from imageApp.models import Images

# Create your models here.

class Product(models.Model):
    busRef = models.ForeignKey(Business, on_delete=models.CASCADE)
    branhRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE, null=True)
    productName = models.CharField(max_length=100)
    productCode = models.CharField(max_length=50)
    productDescription = models.CharField(max_length=500, null=True)
    productCategory = models.CharField(max_length=100)
    belongsToModel = models.CharField(max_length=100, default='Retail & Wholesale Business')
    productImageRef = models.ForeignKey(Images, on_delete=models.DO_NOTHING, null=True)
    measureUnit = models.CharField(max_length=50)
    disbleRef = models.ForeignKey('DisabledProducts', on_delete=models.DO_NOTHING, null=True)
    discountRate = models.FloatField(default=0.0)    
    dateAdded = models.DateField()     
    addedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    retailAndWholesaleRef = models.ForeignKey('salesApp.RetailAndWholesale', on_delete=models.DO_NOTHING, null=True)
    realEstateRef = models.ForeignKey('realEstateApp.RealEstate', on_delete=models.DO_NOTHING, null=True)
    hotelRef = models.ForeignKey('hotelApp.Hotel', on_delete=models.DO_NOTHING, null=True)
    restaurantAndBarRef = models.ForeignKey('restaurantAndBarApp.RestaurantAndBar', on_delete=models.DO_NOTHING, null=True)
    manufacturingRef = models.ForeignKey('manufacturingApp.Manufacturing', on_delete=models.DO_NOTHING, null=True)
    eventManagementRef = models.ForeignKey('eventManagementApp.EventManagement', on_delete=models.DO_NOTHING, null=True)
    transportationRef = models.ForeignKey('transportationApp.Transportation', on_delete=models.DO_NOTHING, null=True)
    farmRef = models.ForeignKey('farmApp.Farm', on_delete=models.DO_NOTHING, null=True)


#Disabled product can't be visible or available for sale
class DisabledProducts(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    productIsDisabled = models.BooleanField(default=False)
    operationBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    date = models.DateTimeField()


# general discount on all goods discount rate
class DiscountRate(models.Model):
    busRef = models.ForeignKey(Business, on_delete=models.CASCADE)
    discount = models.FloatField(default=0.00)
    addedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)





    


    





