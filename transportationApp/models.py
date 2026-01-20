from django.db import models
from businessApp.models import BusinessBranch

# Create your models here.

# for transportation business ==================================================================================  
# this will be created once for each vehicle  
class Transportation(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    vehicleNumber = models.CharField(max_length=20)
    vehicleType = models.CharField(max_length=30) # Truck, Van, Bike, etc
    capacity = models.FloatField(default=0.0) # in tons 
    driverName = models.CharField(max_length=50)
    driverTel = models.CharField(max_length=20)
    scheduleRef = models.ForeignKey('TransportationSchedule', on_delete=models.DO_NOTHING, null=True)



# this will be repeated for each schedule
class TransportationSchedule(models.Model):
    transportationRef = models.ForeignKey(Transportation, on_delete=models.CASCADE)
    scheduleType = models.CharField(max_length=30) # One-way, Round-trip = in and out 
    transportationType = models.CharField(max_length=30) # Goods, Parcel, Passenger
    departureLocation = models.CharField(max_length=100)
    arrivalLocation = models.CharField(max_length=100)
    departureDate = models.DateField()
    arrivalDate = models.DateField()
    distance = models.FloatField(default=0.0) # in km
    fare = models.FloatField(default=0.00) # amount paid for the ticket
    status = models.CharField(max_length=20, default='Scheduled') # Scheduled, In Transit, Cancelled

# this will be repeated for each parcel
class ParcelDetails(models.Model):
    transportationRef = models.ForeignKey(Transportation, on_delete=models.CASCADE)
    senderName = models.CharField(max_length=50)
    senderTel = models.CharField(max_length=20)
    receiverName = models.CharField(max_length=50)
    receiverTel = models.CharField(max_length=20)
    parcelDescription = models.CharField(max_length=200)
    weight = models.FloatField(default=0.0) # in kg
    status = models.CharField(max_length=20, default='In Transit') # In Transit, Delivered, Cancelled


class PassengerDetails(models.Model):
    transportationRef = models.ForeignKey(TransportationSchedule, on_delete=models.CASCADE)
    passengerName = models.CharField(max_length=50, null=True)
    passengerTel = models.CharField(max_length=20)
    seatNumber = models.CharField(max_length=10)
    ticketNumber = models.CharField(max_length=20)
    fare = models.FloatField(default=0.00) # amount paid for the ticket
    status = models.CharField(max_length=20, default='In Transit') # In Transit, Delivered, Cancelled


class PassengerGoodsDetails(models.Model):
    passengerRef = models.ForeignKey(PassengerDetails, on_delete=models.CASCADE)
    goodsDescription = models.CharField(max_length=200)
    weight = models.FloatField(default=0.0) # in kg
    fare = models.FloatField(default=0.00) # amount paid for transporting the goods


class TransportationIncidentReports(models.Model):
    transportationRef = models.ForeignKey(Transportation, on_delete=models.CASCADE)
    reportTitle = models.CharField(max_length=100)
    reportDetails = models.CharField(max_length=300)
    date = models.DateField()

