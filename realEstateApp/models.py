from django.db import models
from businessApp.models import BusinessBranch

# Create your models here.

# for Real estate==============================================================================================
#  There are five main categories of real estate, which include residential, commercial, industrial, raw land, and special use.
class RealEstate(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    estateType = models.CharField(max_length=50) # Residential, Commercial, Industrial, Raw Land, Special Use
    location = models.CharField(max_length=100)  # This can be address or general location
    ownerName = models.CharField(max_length=50)
    ownerTel = models.CharField(max_length=20)
    esateDetailRef = models.ForeignKey('EstateDetails', on_delete=models.CASCADE, null=True)


class EstateDetails(models.Model):
    propertyType = models.CharField(max_length=50) # Apartment, House, Office, Warehouse, Factory, Land, etc
    size = models.FloatField(default=0.0) # in square meters
    price = models.FloatField(default=0.00)
    description = models.CharField(max_length=500, null=True)
    availabilityStatus = models.CharField(max_length=20, default='Available') # Available, Sold, Rented


#An estate viewing is a scheduled appointment to see a property in person to assess its suitability.
# this will be repeated for each viewing appointment
class EstateViewings(models.Model):
    realEstateRef = models.ForeignKey(RealEstate, on_delete=models.CASCADE)
    viewerName = models.CharField(max_length=50)
    viewerTel = models.CharField(max_length=20)
    viewingDate = models.DateField()
    viewingTime = models.TimeField()

# this will be repeated for each rental
# for estate that has been rented out
class EstateRentalRecords(models.Model):
    realEstateRef = models.ForeignKey(RealEstate, on_delete=models.CASCADE)
    renterName = models.CharField(max_length=50)
    renterTel = models.CharField(max_length=20)
    rentAmount = models.FloatField(default=0.00)
    rentStartDate = models.DateField()
    rentEndDate = models.DateField()


# this will be repeated for each sale
# for estate that has been sold
class EstateSalesRecords(models.Model):
    realEstateRef = models.ForeignKey(RealEstate, on_delete=models.CASCADE)
    buyerName = models.CharField(max_length=50)
    buyerTel = models.CharField(max_length=20)
    salePrice = models.FloatField(default=0.00)
    saleDate = models.DateField()


# this will be repeated for each maintenance activity
class EstateMaintenanceRecords(models.Model):
    estateDetailRef = models.ForeignKey(RealEstate, on_delete=models.CASCADE)
    maintenanceDetails = models.CharField(max_length=300)
    maintenanceDate = models.DateField()
    cost = models.FloatField(default=0.00)
