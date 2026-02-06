from django.db import models

# Create your models here.

# sum of all charges
class Bill(models.Model):
    currentBill = models.FloatField(default=0.00)
    arrears = models.FloatField(default=0.00)
    nextBillDate = models.DateField()


# payment detail
class BillPayments(models.Model):
    busID = models.CharField(max_length=50)
    amountPaid = models.FloatField(default=0.00)
    outstandingBalance = models.FloatField(default=0.00)
    transactionID = models.CharField(max_length=50, null=True)  # momo transactionID
    paymentType = models.CharField(max_length=30, default='MoMo') # MoMo, Cash, Bank 
    date = models.DateField()


# charges
class Charges(models.Model):
    busID = models.CharField(max_length=50)
    product = models.CharField(max_length=30, default='Monthly Charges')  # Monthly Charges, SMS Charges, IT Support, etc
    amount = models.FloatField(default=0.00)
    date = models.DateTimeField()


# store the products for referennce when charging
class Products(models.Model):
    productName = models.CharField(max_length=50) 
    chargePerProduct = models.FloatField(default=0.00)
    

    







