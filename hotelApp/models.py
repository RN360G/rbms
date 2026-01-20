from django.db import models
from warehouseApp.models import Product
from businessApp.models import BusinessBranch

# Create your models here.

# for Hotel Business ==========================================================================================================
class Hotel(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    roomNumber = models.CharField(max_length=10)
    roomType = models.CharField(max_length=30) # Single, Double, Suite, etc
    bedType = models.CharField(max_length=30) # King, Queen, Twin, etc
    pricePerHour = models.FloatField(default=0.00) 
    isAvailable = models.BooleanField(default=True)


# WiFi, TV, AC, etc
class RoomAmenities(models.Model):
    hotelRef = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    amenityName = models.CharField(max_length=50)
    amenityDescription = models.CharField(max_length=200, null=True)


class HotelBookings(models.Model):
    hotelRef = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    bookingNumber = models.CharField(max_length=20)
    guestName = models.CharField(max_length=50)
    guestTel = models.CharField(max_length=20)
    checkInDate = models.DateField()
    checkOutDate = models.DateField()
    totalAmount = models.FloatField(default=0.00)
    bookingStatus = models.CharField(max_length=20, default='Booked') # Booked, Checked-in, Checked-out, Cancelled


# services offered by the hotel, e.g: spa, gym, pool, restaurant, bar, laundry, messaging, food, tourism, etc
# this will be created once for each service
class HotelServices(models.Model):
    hotelRef = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    serviceName = models.CharField(max_length=50)
    serviceDescription = models.CharField(max_length=200, null=True)
    servicePrice = models.FloatField(default=0.00)

# this will be repeated for each usage of the service by a guest
class GuestServicesUsage(models.Model):
    hotelServiceRef = models.ForeignKey(HotelServices, on_delete=models.CASCADE)
    guestName = models.CharField(max_length=50)
    guestTel = models.CharField(max_length=20)
    usageDate = models.DateField()
    usageTime = models.TimeField()
    amountCharged = models.FloatField(default=0.00)


class BookingIncidentReports(models.Model):
    hotelBookingRef = models.ForeignKey(HotelBookings, on_delete=models.CASCADE)
    reportTitle = models.CharField(max_length=100)
    reportDetails = models.CharField(max_length=300)
    date = models.DateField()
