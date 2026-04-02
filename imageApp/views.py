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

                
            # convert flyer image to fixed size
            if db.image:
                target_kb = 200
                img = Image.open(db.image.path)

                # Force resize to exact dimensions (e.g., 800x400)
                fixedSize = (800, 400)
                img = img.resize(fixedSize, Image.Resampling.LANCZOS)

                quality = 85
                while True:
                    # If flyer has transparency, keep PNG; otherwise use JPEG for better compression
                    if img.mode in ("RGBA", "LA"):
                        img.save(db.image.path, format='PNG', optimize=True)
                    else:
                        img.save(db.image.path, format='JPEG', quality=quality, optimize=True)

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

            # convert flyer image to fixed size
            if db.image:
                target_kb = 200
                img = Image.open(db.image.path)

                # Force resize to exact dimensions (e.g., 800x400)
                fixedSize = (800, 400)
                img = img.resize(fixedSize, Image.Resampling.LANCZOS)

                quality = 85
                while True:
                    # If flyer has transparency, keep PNG; otherwise use JPEG for better compression
                    if img.mode in ("RGBA", "LA"):
                        img.save(db.image.path, format='PNG', optimize=True)
                    else:
                        img.save(db.image.path, format='JPEG', quality=quality, optimize=True)

                    size_kb = os.path.getsize(db.image.path) / 1024
                    if size_kb <= target_kb or quality <= 20:
                        break
                    quality -= 5


    def uploadBusinessFlyer(self,request, file):
        with transaction.atomic():
            fs = FileSystemStorage()
            eFile = str(file.name)
            eLastDot = eFile.rfind('.')
            fileExtension = eFile[eLastDot + 1:]
            
            business = logV.loginSessions(request, 'business')
            user = logV.loginSessions(request, 'user')
            
            # Check if logo already exists for this business
            check = Images.objects.filter(Q(busRef=business) & Q(imgType='logo'))
            
            name = str(business.busID) + '_logo'
            filename = fs.save(name + '.' + fileExtension, file)
            
            db = None
            if check.exists():
                db = check[0]
                # delete existing logo file
                fs.delete(db.image.path)
            else:
                db = Images()
            
            db.busRef = business
            db.userRef = user
            db.uniqueID = filename
            db.subjectID = business.busID
            db.imgType = 'logo'
            db.image = filename
            db.extention = fileExtension
            db.date = dt.datetime.now()
            db.save()

            # convert flyer image to fixed size
            if db.image:
                target_kb = 200
                img = Image.open(db.image.path)

                # Force resize to exact dimensions (e.g., 800x400)
                fixedSize = (800, 400)
                img = img.resize(fixedSize, Image.Resampling.LANCZOS)

                quality = 85
                while True:
                    # If flyer has transparency, keep PNG; otherwise use JPEG for better compression
                    if img.mode in ("RGBA", "LA"):
                        img.save(db.image.path, format='PNG', optimize=True)
                    else:
                        img.save(db.image.path, format='JPEG', quality=quality, optimize=True)

                    size_kb = os.path.getsize(db.image.path) / 1024
                    if size_kb <= target_kb or quality <= 20:
                        break
                    quality -= 5
            return db
        

    def uploadProfileUser(self, request, file):
        with transaction.atomic():
            fs = FileSystemStorage()
            eFile = str(file.name)
            eLastDot = eFile.rfind('.')
            fileExtension = eFile[eLastDot + 1:]

            business = logV.loginSessions(request, 'business')
            user = logV.loginSessions(request, 'user')

            # Check if profile picture already exists for this user
            check = Images.objects.filter(Q(userRef=user) & Q(imgType='profile'))

            name = str(user.userID) + '_profile'
            filename = fs.save(name + '.' + fileExtension, file)

            db = None
            if check.exists():
                db = check[0]
                # delete existing profile picture file
                fs.delete(db.image.path)
            else:
                db = Images()
            db.busRef = business
            db.userRef = user
            db.uniqueID = filename
            db.subjectID = user.userID
            db.imgType = 'profile'
            db.image = filename
            db.extention = fileExtension
            db.date = dt.datetime.now()
            db.save()

            # --- Resize and compress to fixed size ---
            if db.image:
                target_kb = 200
                img = Image.open(db.image.path)

                # Force resize to exact dimensions (e.g., 400x400 for square profile pics)
                fixedSize = (400, 400)
                img = img.resize(fixedSize, Image.Resampling.LANCZOS)

                quality = 85
                while True:
                    # If profile pic has transparency, keep PNG; otherwise use JPEG
                    if img.mode in ("RGBA", "LA"):
                        img.save(db.image.path, format='PNG', optimize=True)
                    else:
                        img.save(db.image.path, format='JPEG', quality=quality, optimize=True)

                    size_kb = os.path.getsize(db.image.path) / 1024
                    if size_kb <= target_kb or quality <= 20:
                        break
                    quality -= 5

            # Store image path in session
            request.session['profileImage'] = db.image.url



        

        





