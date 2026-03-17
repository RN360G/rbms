from django.db import models
from businessApp.models import BusinessBranch
from warehouseApp.models import Product

# Create your models here.

class CustomerInfor(models.Model):
    tel = models.CharField(max_length=30)
    pin = models.CharField(max_length=300)
    customerName = models.CharField(max_length=50)
    status = models.CharField(max_length=15, default='Pending') # Pending, Verified


# customer cart
class CustomerAddToCart(models.Model):
    branhRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE, null=True)
    customerTel = models.CharField(max_length=30)
    productRef = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)
    unitPrice = models.FloatField()
    discount = models.FloatField(default=0.00)
    totalPrice = models.FloatField()
    status = models.CharField(max_length=20, default='Waiting Payment Request') # Waiting Payment Request -> Pending Payment Request -> Request Accepted ->Payment Confirmed -> Packaged -> Delivered
    orderID = models.CharField(max_length=6)
    acceptedCode = models.CharField(max_length=6, default='') # this code will be inserted when your payment request is acceped.
    batchCode = models.CharField(max_length=20)
    paidToAccount = models.CharField(max_length=30, default="") 
    date = models.DateTimeField()


# current Cart Batch
class CurrentCartBatch(models.Model):
    batchCode = models.CharField(max_length=20)
    customerTel = models.CharField(max_length=30)
    status = models.CharField(max_length=20, default='Waiting Payment Request') # Waiting Payment Request -> Pending Payment Request -> Request Accepted ->Payment Confirmed -> Packaged -> Delivered 


# store customers Name for the first time
class DeliveryAddress(models.Model):
    customerTel = models.CharField(max_length=30)
    customerName = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
