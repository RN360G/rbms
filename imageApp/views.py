from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import random as rd
import datetime as dt
from imageApp.models import Images, OtherFiles
from businessApp.models import Business
from usersApp.models import UserRef
from django.db.models import Q, Count
from django.db import transaction
from warehouseApp.models import Product
from richnet360.views import BillBusiness
from PIL import Image, ImageOps
import cv2
import loginAndOutApp.views as logV
import os


# Create your views here.

class ImageUpload():
    def uploadProductFlyer(self,request, file, productCode):
        with transaction.atomic():
            fs = FileSystemStorage()
            eFile = str(file.name)
            eLastDot = eFile.rfind('.')
            fileExtension = eFile[eLastDot + 1:]        
            check = Images.objects.filter(Q(subjectID=productCode) & Q(busRef=logV.loginSessions(request, 'business')))
            name = str(logV.loginSessions(request, 'business').busID) + '' + str(productCode)
            filename = fs.save(name + '.' + 'png', file) 
            db = None
            if check.exists():
                db = check[0]
                # delete existng image file
                fs.delete(db.image.path) 

                db.busRef = logV.loginSessions(request, 'business')
                db.userRef = logV.loginSessions(request, 'user')
                db.uniqueID = filename
                db.subjectID = productCode
                db.imgType = 'product'
                db.image = filename
                db.extention = fileExtension
                db.date = dt.datetime.now()
                db.save()            
            else:
                db = Images()
                db.busRef = logV.loginSessions(request, 'business')
                db.userRef = logV.loginSessions(request, 'user')
                db.uniqueID = filename
                db.subjectID = productCode
                db.imgType = 'product'
                db.image = filename
                db.extention = fileExtension
                db.date = dt.datetime.now()
                db.save()

                
            # convert image size
            if db.image:
                target_kb=200
                img = Image.open(db.image.path)
                # Define max size and resize 
                maxSize = (800, 400)
                img = ImageOps.fit(img, maxSize, Image.Resampling.LANCZOS)
                quality = 85
                while True:
                    img.save(db.image.path, format='png', quality=quality, optimize=True)
                    size_kb = os.path.getsize(db.image.path) / 1024
                    if size_kb <= target_kb or quality <= 20:
                        break
                    quality -= 5  
            # bill the business for uploading the flyer
            BillBusiness.chargesBaseOnUsage(self, request, db.busRef.busID, 'Images Upload Charges')        
            return db
        

    # download other images of the product
    def uploadProductImages(self, request, file, productCode):
        with transaction.atomic():
            image = Images.objects.get(
                Q(subjectID=productCode) & Q(busRef=logV.loginSessions(request, 'business'))
            )
            fs = FileSystemStorage()
            eFile = str(file.name)
            eLastDot = eFile.rfind('.')
            fileExtension = eFile[eLastDot + 1:]        

            # Get all images for this product, oldest first
            check = OtherFiles.objects.filter(
                Q(uniqueID=productCode) & Q(imageRef__busRef=logV.loginSessions(request, 'business'))
            ).order_by("date")

            # If more than or equal to 3, delete the oldest one
            if check.count() >= 3:
                oldest = check.first()
                if oldest.image:
                    try:
                        # delete the file from storage
                        fs.delete(oldest.image.path)
                    except Exception:
                        pass
                oldest.delete()

            # Save new image
            name = (
                str(logV.loginSessions(request, 'business').busID)
                + str(productCode)
                + str(rd.randrange(100000, 999999))
                + "_"
                + dt.datetime.now().strftime("%Y%m%d%H%M%S")
            )
            filename = fs.save(name + ".png", file)

            db = OtherFiles()
            db.imageRef = image
            db.uniqueID = name
            db.image = filename
            db.extention = fileExtension
            db.date = dt.datetime.now()
            db.save()

            # convert image size
            if db.image:
                target_kb = 200
                img = Image.open(db.image.path)
                maxSize = (800, 400)
                img = ImageOps.fit(img, maxSize, Image.Resampling.LANCZOS)
                quality = 85
                while True:
                    img.save(db.image.path, format="png", quality=quality, optimize=True)
                    size_kb = os.path.getsize(db.image.path) / 1024
                    if size_kb <= target_kb or quality <= 20:
                        break
                    quality -= 5




        

        





