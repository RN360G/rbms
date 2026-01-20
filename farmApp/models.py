from django.db import models
from businessApp.models import BusinessBranch


# Create your models here.

# for Farm Business ===========================================================================================
class Farm(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    farmType = models.CharField(max_length=50) # Crop farming, Livestock farming, Mixed farming, etc
    location = models.CharField(max_length=100)
    farmSize = models.FloatField(default=0.0) # in acres 
    LivestockRef = models.ForeignKey('Livestock', on_delete=models.CASCADE, null=True)
    cropRef = models.ForeignKey('Crop', on_delete=models.CASCADE, null=True)


class FarmSeason(models.Model):
    farmRef = models.ForeignKey(Farm, on_delete=models.CASCADE)
    seasonName = models.CharField(max_length=50) # e.g: Spring, Summer, Autumn, Winter, Dry season, Rainy season, etc
    startDate = models.DateField()
    endDate = models.DateField()


# crop farming
class Crop(models.Model):
    farmRef = models.ForeignKey(Farm, on_delete=models.CASCADE)
    cropType = models.CharField(max_length=50) # e.g: Maize, Wheat, Rice, Vegetables, Fruits, etc


# this will be created once for each batch of crops
class BatchOfCrops(models.Model):   
    cropRef = models.ForeignKey(Crop, on_delete=models.CASCADE)
    batchNumber = models.CharField(max_length=50)
    areaPlanted = models.FloatField(default=0.0) # in acres
    datePlanted = models.DateField()
    expectedHarvestDate = models.DateField()
    actualHarvestDate = models.DateField(null=True)
    yieldQuantity = models.FloatField(default=0.0) # in tons
    yieldAccuracy = models.CharField(max_length=20, default="Estimated") # Estimated, Actual


# livestock farming
class Livestock(models.Model):
    farmRef = models.ForeignKey(Farm, on_delete=models.CASCADE)
    animalType = models.CharField(max_length=50) # Cattle, Sheep, Goats, Pigs, Poultry, etc
    totalAnimals = models.IntegerField(default=0)


# this will be created once for each batch of livestock
class BatchOfLivestock(models.Model):
    livestockRef = models.ForeignKey(Livestock, on_delete=models.CASCADE)
    batchNumber = models.CharField(max_length=50)
    numberOfAnimals = models.IntegerField(default=0)
    dateAdded = models.DateField()


# Milk, Meat, Eggs, Wool, etc
class LivestockByProduct(models.Model):
    livestockRef = models.ForeignKey(Livestock, on_delete=models.CASCADE)
    productType = models.CharField(max_length=50) # Milk, Meat, Eggs, Wool, etc
    qtyType = models.CharField(max_length=20) # liters, kg, pieces, crate, etc
    totalProduced = models.FloatField(default=0.0) # in liters, kg, pieces, etc
    productionDate = models.DateField()


# disease, injury, parasite infestation, etc
class HealthRecords(models.Model):
    farmRef = models.ForeignKey(Farm, on_delete=models.CASCADE)
    recordTitle = models.CharField(max_length=100)
    recordDetails = models.CharField(max_length=300)
    dateReported = models.DateField()
    dateTreated = models.DateField(null=True)


# daily activities on the farm, e.g: planting, watering, fertilizing, harvesting, feeding, milking, cleaning, etc
# this will be created once for each activity
class DailyFarmActivities(models.Model):
    farmRef = models.ForeignKey(FarmSeason, on_delete=models.CASCADE)
    activityTitle = models.CharField(max_length=100)
    activityDetails = models.CharField(max_length=300)
    activityDateAndTime = models.DateTimeField()
    cost = models.FloatField(default=0.00)
    activityBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)



# this will be repeated for each time an activity is performed
class PerfomedFarmActivities(models.Model):
    dailyActivityRef = models.ForeignKey(DailyFarmActivities, on_delete=models.CASCADE)
    datePerformed = models.DateField()
    cost = models.FloatField(default=0.00)
    performedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


class FarmEquipment(models.Model):
    farmRef = models.ForeignKey(Farm, on_delete=models.CASCADE)
    equipmentName = models.CharField(max_length=50)
    equipmentType = models.CharField(max_length=50) # Tractor, Plough, Harrow, Seeder, Sprayer, etc
    dateAcquired = models.DateField()
    cost = models.FloatField(default=0.00)
    state = models.CharField(max_length=20, default='Good') # Good, Fair, Poor


# this will be repeated for each maintenance activity
class EquipmentMaintenanceRecords(models.Model):
    farmEquipmentRef = models.ForeignKey(FarmEquipment, on_delete=models.CASCADE)
    maintenanceDetails = models.CharField(max_length=300)
    maintenanceDate = models.DateField()
    cost = models.FloatField(default=0.00)
