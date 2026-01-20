from django.db import models
from usersApp.models import UserRef
from businessApp.models import Business

# Create your models here.

class Images(models.Model):
    busRef = models.ForeignKey(Business, on_delete=models.CASCADE)
    userRef = models.ForeignKey(UserRef, on_delete=models.CASCADE)
    uniqueID = models.CharField(max_length=50, unique=True)
    subjectID = models.CharField(max_length=50) # the subject could be product, flyer, business, profile
    image = models.ImageField()
    extention = models.CharField(max_length=6)
    imgType = models.CharField(max_length=15, default='product')  # profile, logo, flyer, product
    date = models.DateTimeField()


# when the product contains more images
class OtherFiles(models.Model):
    imageRef = models.ForeignKey(Images, on_delete=models.CASCADE)
    uniqueID = models.CharField(max_length=50, unique=True)
    image = models.ImageField()
    extention = models.CharField(max_length=6)
    date = models.DateTimeField()




