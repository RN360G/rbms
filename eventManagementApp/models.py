from django.db import models
from businessApp.models import BusinessBranch

# Create your models here.
# for Event Management and Ticketing===========================================================================================
class EventManagement(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    eventType = models.CharField(max_length=50) # Concert, Conference, Sports, Festival, etc
    eventLocation = models.CharField(max_length=100)
    organizerName = models.CharField(max_length=50)
    organizerTel = models.CharField(max_length=20)
    totalTickets = models.IntegerField(default=0)
    totalSeat = models.IntegerField(default=0)
    numberOfSession = models.IntegerField(default=1) # for multi-session events
    ticketsSold = models.IntegerField(default=0)
    ticketsAvailable = models.IntegerField(default=0)


# Event schedules, e.g: Opening ceremony, Keynote speech, Performance, etc
# this could also be used for multi-day or multi-session  or multi-venue events
class EventSchedules(models.Model):
    eventRef = models.ForeignKey(EventManagement, on_delete=models.CASCADE)
    scheduleTitle = models.CharField(max_length=100)
    scheduleDetails = models.CharField(max_length=300)
    scheduleDate = models.DateField()
    scheduleTime = models.TimeField()


# Ticket categories, e.g: VIP, General, Balcony, etc
class TicketCategories(models.Model):
    eventRef = models.ForeignKey(EventManagement, on_delete=models.CASCADE)
    categoryName = models.CharField(max_length=50) # VIP, General, Balcony, etc
    categoryDescription = models.CharField(max_length=200, null=True)
    ticketPrice = models.FloatField(default=0.00)
    totalTickets = models.IntegerField(default=0)
    ticketsSold = models.IntegerField(default=0)
    ticketsAvailable = models.IntegerField(default=0)


# Embossed ticket details all tickets will have unique details
class EmbossedTicketDetails(models.Model):
    ticketCategoryRef = models.ForeignKey(TicketCategories, on_delete=models.CASCADE)
    ticketID = models.CharField(max_length=50)
    embossingDetails = models.CharField(max_length=200) # e.g: hologram, barcode, QR code, serial number, etc
    qrCodeData = models.CharField(max_length=200, null=True)
    isSold = models.BooleanField(default=False)
    purchaserRef = models.ForeignKey('TicketsPurchaser', on_delete=models.CASCADE, null=True)


class SeatNumbering(models.Model):
    eventRef = models.ForeignKey(EventManagement, on_delete=models.CASCADE)
    seatNumber = models.CharField(max_length=10)


# Ticket Purchaser details
class TicketsPurchaser(models.Model):
    ticketsRef = models.ForeignKey(EmbossedTicketDetails, on_delete=models.CASCADE)
    ticketNumber = models.CharField(max_length=20)
    purchaserName = models.CharField(max_length=50)
    purchaserTel = models.CharField(max_length=20)
    purchaseDate = models.DateField()
    seatNumber = models.CharField(max_length=10, null=True)
    ticketStatus = models.CharField(max_length=20, default='Valid') # Valid, Used, Cancelled