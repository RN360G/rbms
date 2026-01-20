from django.db import models
from warehouseApp.models import Product
from businessApp.models import BusinessBranch

# Create your models here.

# Manufacturing Business=======================================================================================
class Manufacturing(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    ProductCode = models.CharField(max_length=50)
    ProductDescription = models.CharField(max_length=200, null=True)
    productType = models.CharField(max_length=50, default='Raw Material') # Raw Material , Fisnished Product
    rawMaterialRef = models.ForeignKey('RawMaterial', on_delete=models.DO_NOTHING, null=True)
    finishedProductRef = models.ForeignKey('FinishedProduct', on_delete=models.DO_NOTHING, null=True)


# records on raw material
class RawMaterial(models.Model):
    manufacturingRef = models.ForeignKey(Manufacturing, on_delete=models.CASCADE)
    stockAvailable = models.FloatField(default=0.0)
    costPerStock = models.FloatField(default=0.00)
    restockLevel = models.FloatField(default=0)


# records on finished product
class FinishedProduct(models.Model):
    manufacturingRef = models.ForeignKey(Manufacturing, on_delete=models.CASCADE)
    stockAvailable = models.FloatField(default=0.0)
    costPricePerStock = models.FloatField(default=0.00)
    sellingPerStock = models.FloatField(default=0.00)
    restockLevel = models.FloatField(default=0)


class DamageProductsRecords(models.Model):
    manufacturingRef = models.ForeignKey(Manufacturing, on_delete=models.CASCADE)
    productType = models.CharField(max_length=50, default='Raw Material') # Raw Material , Fisnished Product
    quantityDamage = models.FloatField(default=0.0)
    costInvolve = models.FloatField(default=0.00)
    

# this will be created once for each batch of manufactured products
class BatchOfManufacturedProducts(models.Model):
    manufacturingRef = models.ForeignKey(Manufacturing, on_delete=models.CASCADE)
    batchNumber = models.CharField(max_length=50)
    expectedQuantity = models.FloatField(default=0.0) # in pieces, kg, litres, etc
    actualQuantityProduced = models.FloatField(default=0.0) # in pieces, kg, litres, etc
    productionDate = models.DateField()
    expectedCompletionDate = models.DateField()
    actualCompletionDate = models.DateField(null=True)


# processes involved in manufacturing the products in the batch
class ManufacturingProcesses(models.Model):
    manufacturingRef = models.ForeignKey(BatchOfManufacturedProducts, on_delete=models.CASCADE)
    processName = models.CharField(max_length=100)
    processDescription = models.CharField(max_length=300, null=True)
    processPercentage = models.FloatField(default=0.0) # percentage of the total manufacturing process


# operations involved in each manufacturing process
class ProcessOperations(models.Model):
    manufacturingProcessRef = models.ForeignKey(ManufacturingProcesses, on_delete=models.CASCADE)
    operationName = models.CharField(max_length=100)
    operationDescription = models.CharField(max_length=300, null=True)
    operationDate = models.DateField()
    cost = models.FloatField(default=0.00)
    operationBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# raw materials used in each manufacturing operation
class RawMaterialsUsed(models.Model):
    manufacturingRef = models.ForeignKey(ProcessOperations, on_delete=models.CASCADE)
    ProductRef = models.ForeignKey(Product, on_delete=models.CASCADE)
    materialName = models.CharField(max_length=100)
    quantityUsed = models.FloatField(default=0.0) # in pieces, kg, litres, etc
    costPerUnit = models.FloatField(default=0.00)
    totalCost = models.FloatField(default=0.00)

# request for raw materials needed for manufacturing from wharehouse
class RequestedRawMaterials(models.Model):
    manufacturingRef = models.ForeignKey(BatchOfManufacturedProducts, on_delete=models.CASCADE)
    ProductRef = models.ForeignKey(Product, on_delete=models.CASCADE)   
    materialName = models.CharField(max_length=100)
    quantityRequested = models.FloatField(default=0.0) # in pieces, kg, litres, etc
    requestStatus = models.CharField(max_length=20, default='Pending') # Pending, Approved, Rejected    
    requestDate = models.DateField()
    requestedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    respondedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING, related_name='responder', null=True)
    respondDate = models.DateField(null=True)


# storage details of finished products in the warehouse
# this will be created once for each batch of finished products stored in the warehouse
class FinisedProductsStorageInWarehouse(models.Model):
    manufacturingRef = models.ForeignKey(BatchOfManufacturedProducts, on_delete=models.CASCADE)
    storageLocation = models.CharField(max_length=100)
    quantityStored = models.FloatField(default=0.0) # in pieces, kg, litres, etc
    dateStored = models.DateField()
    storedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# incident reports related to manufacturing processes
class ManufacturingIncidentReports(models.Model):
    manufacturingRef = models.ForeignKey(BatchOfManufacturedProducts, on_delete=models.CASCADE)
    reportTitle = models.CharField(max_length=100)
    reportDetails = models.CharField(max_length=300)
    costInvolved = models.FloatField(default=0.00)
    date = models.DateField()
