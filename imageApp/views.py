from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import random as rd
import datetime as dt
from imageApp.models import Images
from businessApp.models import Business
from usersApp.models import UserRef
from django.db.models import Q, Count
from django.db import transaction
import cv2

# Create your views here.

class ImageUpload():

    imageID = None
    uploadType = 'product'
    fileName = None
    userRef = None
    busRef = None
    fs = None
    request = None
    fileExtention = ''

    def __init__(self, request, uploadType):
        self.request = request
        self.busRef = Business.objects.get(Q(busID=request.session['busID']))
        self.userRef = UserRef.objects.get(Q(userID=request.session['userID']))
        self.fs = FileSystemStorage()

        self.uploadType = uploadType
        if self.uploadType == 'product':
            self.fileName = str(request.session['busID']) + '' + str(rd.randrange(0,1000)) + '' + str(rd.randrange(1000,9999)) + '' + str(dt.datetime.now().year) + '' + str(dt.datetime.now().month) + '' + str(dt.datetime.now().day) + '' + str(dt.datetime.now().hour) + '' + str(dt.datetime.now().minute) + '' + str(dt.datetime.now().second)
        elif self.uploadType == 'profile':
            self.fileName = str(request.session['userID'])
        elif self.uploadType == 'logo':
            self.fileName = str(request.session['busID'])
        elif self.uploadType == 'flyer':
            self.fileName = str(request.session['busID']) + '' + str(rd.randrange(0,1000)) + '' + str(rd.randrange(1000,9999)) + '' + str(dt.datetime.now().year) + '' + str(dt.datetime.now().month) + '' + str(dt.datetime.now().day) + '' + str(dt.datetime.now().hour) + '' + str(dt.datetime.now().minute) + '' + str(dt.datetime.now().second)

    def upload(self, file, subjectID=None):
        eFile = str(file.name)
        eLastDot = eFile.rfind('.')
        self.fileExtension = eFile[eLastDot + 1:]

        if self.uploadType == 'product':
            count = Images.objects.filter(Q(subjectID=subjectID)).annotate(Count('subjectID'))
            if int(count.count()) + 1 < 6:
                self.storeDetails(subjectID)
                self.fileName = self.fs.save(self.fileName + '.' + self.fileExtension, file)
            else:
                pass
        elif self.uploadType == 'flyer':
            count = Images.objects.filter(Q(subjectID=subjectID)).annotate(Count('subjectID'))
            if int(count.count()) + 1 < 11:
                self.storeDetails(str(self.request.session['busID']) + 'flyer')
                self.fileName = self.fs.save(self.fileName + '.' + self.fileExtension, file)
            else:
                pass
        elif self.uploadType == 'logo':
            count = Images.objects.filter(Q(subjectID=subjectID)).annotate(Count('subjectID'))
            if int(count.count()) + 1 < 2:
                self.storeDetails(str(self.request.session['busID']) + 'logo')
                self.fileName = self.fs.save(self.fileName + '.' + self.fileExtension, file)
            else:
                pass
        elif self.uploadType == 'profile':
            count = Images.objects.filter(Q(subjectID=subjectID)).annotate(Count('subjectID'))
            if int(count.count()) + 1 < 2:
                self.storeDetails(subjectID)
                self.fileName = self.fs.save(self.fileName + '.' + self.fileExtension, file)
            else:
                pass


    def storeDetails(self, subjectID=None):
        db = Images()
        db.busRef = self.busRef
        db.userRef = self.userRef
        db.uniqueID = self.fileName
        if subjectID ==None:
            db.subjectID = self.fileName
        else:
            db.subjectID = subjectID
        db.imgType = self.uploadType
        db.image = str(self.fileName) + '.' + str(self.fileExtension)
        db.extention = self.fileExtension
        db.date = dt.datetime.now()
        db.save()


    def update(self, id, file):
        eFile = str(file.name)
        eLastDot = eFile.rfind('.')
        fileExtension = eFile[eLastDot + 1:]
    
        self.imageID = id
        self.fileName = self.fs.save(self.fileName + '.' + fileExtension, file)

    def delete(self, id):
        self.imageID = id

        




