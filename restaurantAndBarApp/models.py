from django.db import models
from businessApp.models import BusinessBranch
# Create your models here.

# for Restaurant and Bar Business================================================================================
class RestaurantAndBar(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    itemCode = models.CharField(max_length=50)
    itemType = models.CharField(max_length=50) # Food, Beverage, Alcoholic Beverage, etc
    itemPrice = models.FloatField(default=0.00)
    isAvailable = models.BooleanField(default=True)
    

# customer orders
# this order can contain multiple items from the restaurant and bar
class CustomerOrders(models.Model):
    restaurantRef = models.ForeignKey(RestaurantAndBar, on_delete=models.CASCADE)    
    orderNumber = models.CharField(max_length=20)
    customerName = models.CharField(max_length=50)
    customerTel = models.CharField(max_length=20)
    totalPrice = models.FloatField(default=0.00)
    orderStatus = models.CharField(max_length=20, default='Pending') # Pending, In Progress, Completed, Cancelled, Delivered
    orderType = models.CharField(max_length=20, default='Dine-in') # Dine-in, Takeaway, Delivery
    orderDate = models.DateField()
    modeOfPayment = models.CharField(max_length=20, default='Cash') # Cash, Mobile Money, Card, etc
    deliveryGuyRef = models.ForeignKey('DeliveryGuys', on_delete=models.CASCADE, null=True)



# list of items in each customer order
class CustomerOrderItems(models.Model):
    orderRef = models.ForeignKey(CustomerOrders, on_delete=models.CASCADE)
    itemRef = models.ForeignKey(RestaurantAndBar, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    totalPrice = models.FloatField(default=0.00) # quantity * itemPrice


# delivery guys for restaurant and bar deliveries
class DeliveryGuys(models.Model):
    userRef = models.ForeignKey('usersApp.UserRef', on_delete=models.CASCADE)
    vehicleType = models.CharField(max_length=30) # Bike, Car, Van, etc
    vehicleNumber = models.CharField(max_length=20)


class IncidentReportsRestaurantAndBar(models.Model):
    restaurantRef = models.ForeignKey(RestaurantAndBar, on_delete=models.CASCADE)
    reportTitle = models.CharField(max_length=100)
    reportDetails = models.CharField(max_length=300)
    date = models.DateField()
