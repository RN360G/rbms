from django.db import models

from warehouseApp.models import Product
from salesApp.models import CashOnhand

class OperationExpenses(models.Model):
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    expenseType = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    dateIncurred = models.DateField()
    description = models.CharField(max_length=255, null=True)
    transactionIsConfirmed = models.BooleanField(default=False)
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


class Asset(models.Model):  
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    assetType = models.CharField(max_length=50)  # e.g., Fixed, Current
    assetInOut = models.CharField(max_length=10)  # Addition or Disposal
    assetName = models.CharField(max_length=100)
    assetValue = models.DecimalField(max_digits=15, decimal_places=2)
    dateAcquired = models.DateField()
    description = models.CharField(max_length=255, null=True)
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


class Liability(models.Model):  
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    liabilityType = models.CharField(max_length=50)  # e.g., Short-term, Long-term
    liabilityInOut = models.CharField(max_length=10)  # Addition or Settlement
    liabilityName = models.CharField(max_length=100)
    liabilityAmount = models.DecimalField(max_digits=15, decimal_places=2)
    dateIncurred = models.DateField()
    description = models.CharField(max_length=255, null=True)
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


class Equity(models.Model): 
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    equityType = models.CharField(max_length=50)  # e.g., Owner's Capital, Retained Earnings
    equityInOut = models.CharField(max_length=10)  # Addition or Withdrawal
    equityName = models.CharField(max_length=100)
    equityAmount = models.DecimalField(max_digits=15, decimal_places=2)
    dateRecorded = models.DateField()
    description = models.CharField(max_length=255, null=True)
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# accounts =============================================================================
class Accounts(models.Model):
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE, null=True)
    accountType = models.CharField(max_length=15) # Business Account, Branch Account     
    accountName = models.CharField(max_length=50)
    accountNumber = models.CharField(unique=True, max_length=20)
    accountBalance = models.FloatField(default=0.00)


# transactions on the accounts
class AccountTransaction(models.Model):
    accountRef = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    transactionType = models.CharField(max_length=10) # Credit, Debit
    transactionID = models.CharField(max_length=50)
    amount = models.FloatField(default=0.00)
    balance = models.FloatField(default=0.00)
    narration = models.CharField(max_length=500)
    date = models.DateTimeField()
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# this contains users wh can access the various accounts
class AccountAccess(models.Model):
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE, null=True)
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    accountRef = models.ForeignKey(Accounts, on_delete=models.CASCADE)


class DailyProfitLoss(models.Model):
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    date = models.DateField()
    totalRevenue = models.DecimalField(max_digits=15, decimal_places=2)
    totalExpenses = models.DecimalField(max_digits=15, decimal_places=2)
    netProfit = models.DecimalField(max_digits=15, decimal_places=2)
    

# add denominations
class CashDenominations(models.Model):
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    addedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    cash200 = models.IntegerField(default=0)
    cash100 = models.IntegerField(default=0)
    cash50 = models.IntegerField(default=0)
    cash20 = models.IntegerField(default=0)
    cash10 = models.IntegerField(default=0)
    cash5 = models.IntegerField(default=0)
    cash2 = models.IntegerField(default=0)
    cash1 = models.IntegerField(default=0)
    coins50pesewas = models.IntegerField(default=0)
    coins20pesewas = models.IntegerField(default=0)
    coins10pesewas = models.IntegerField(default=0)
    coins5pesewas = models.IntegerField(default=0)
    coins1pesewa = models.IntegerField(default=0)
    totalCash = models.FloatField(default=0.00)
    cash200Total = models.FloatField(default=0.00)
    cash100Total = models.FloatField(default=0.00)
    cash50Total = models.FloatField(default=0.00)
    cash20Total = models.FloatField(default=0.00)
    cash10Total = models.FloatField(default=0.00)
    cash5Total = models.FloatField(default=0.00)
    cash2Total = models.FloatField(default=0.00)
    cash1Total = models.FloatField(default=0.00)
    coins50pesewasTotal = models.FloatField(default=0.00)
    coins20pesewasTotal = models.FloatField(default=0.00)
    coins10pesewasTotal = models.FloatField(default=0.00)
    coins5pesewasTotal = models.FloatField(default=0.00)
    coins1pesewaTotal = models.FloatField(default=0.00)
    CashOnhandRef = models.ForeignKey(CashOnhand, on_delete=models.DO_NOTHING, null=True)
    status = models.CharField(max_length=20, default="Fund not transfered")


# record of fund transfers between accounts    
class TransferFundsRecord(models.Model):
    transferType = models.CharField(max_length=10)  # Transfering, Receiving
    fromAccountRef = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='from_account')
    toAccountRef = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='to_account')
    transactionID = models.CharField(max_length=50)
    amount = models.FloatField(default=0.00)
    narration = models.CharField(max_length=500)
    date = models.DateTimeField()
    transerStatus = models.CharField(max_length=20)  # Pending, Confirmed, Rejected
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING, related_name='entered_by')
    confirmBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING, null=True, related_name='confirm_by')


# total overs and shortages in the account
class OversAndShortages(models.Model):
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    overAmount = models.FloatField(default=0.00)
    shortageAmount = models.FloatField(default=0.00)
    fromAccountRef = models.ForeignKey(Accounts, on_delete=models.CASCADE)


# detailed records of overs and shortages
class OversAndShortagesRecord(models.Model):
    oversAndShortagesRef = models.ForeignKey(OversAndShortages, on_delete=models.CASCADE)
    transactionType = models.CharField(max_length=10)  # Over, Shortage
    amount = models.FloatField(default=0.00)
    date = models.DateTimeField()


# shortage payments records
class ShortagePaymentRecord(models.Model):
    oversAndShortagesRef = models.ForeignKey(OversAndShortages, on_delete=models.CASCADE)
    paymentType = models.CharField(max_length=20)  # Make Payment, Clear Shortage
    amount = models.FloatField(default=0.00)
    balance = models.FloatField(default=0.00)
    narration = models.CharField(max_length=500)
    date = models.DateTimeField()
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# overs widhdrawal records
class OverWithdrawalRecord(models.Model):
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    accountRef = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    oversAndShortagesRef = models.ForeignKey(OversAndShortages, on_delete=models.CASCADE)
    withdrawalType = models.CharField(max_length=20)  # Moved, Deposit
    amount = models.FloatField(default=0.00)
    balance = models.FloatField(default=0.00)
    narration = models.CharField(max_length=500)
    date = models.DateTimeField()
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# suspense account for inter branch and business transactions
class SuspenseAccount(models.Model):
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    option = models.CharField(max_length=20, default='cashOnHand')  # cashOnHand, interBranch, branchToBusiness
    transactionID = models.CharField(max_length=50)
    fromBranch = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE, null=True, related_name='from_branch')
    toBranch = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE, null=True, related_name='to_branch')
    fromAccountRef = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='suspense_from_account')
    toAccountRef = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='suspense_to_account')
    amount = models.FloatField(default=0.00)
    oversAmount = models.FloatField(default=0.00) 
    shortageAmount = models.FloatField(default=0.00) 
    description = models.CharField(max_length=255, null=True)
    date = models.DateTimeField()
    enteredBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# PayRoll ==========================================
class PayRoll(models.Model):
    busRef = models.ForeignKey('businessApp.Business', on_delete=models.CASCADE)
    firstName = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    staffID = models.CharField(max_length=50)
    tel = models.CharField(max_length=20)
    ssnit = models.CharField(max_length=20)
    dob = models.CharField(max_length=15)
    position = models.CharField(max_length=50)
    wageType = models.CharField(max_length=20) # Annual Salary(Salary), hourly wages 
    currentSalary = models.FloatField(default=0.00)


#online payment accounts
class OnlineAccounts(models.Model):
    branchRef = models.ForeignKey('businessApp.BusinessBranch', on_delete=models.CASCADE)
    accountNumber = models.CharField(max_length=30)
    accountName = models.CharField(max_length=50)
    accountType = models.CharField(max_length=15, default='Mobile Money Account') # Mobile Money Account, Bank Account
    subscriber = models.CharField(max_length=30, default="")
    bankName = models.CharField(max_length=30, default="")
    bankBranchName = models.CharField(max_length=30, default="")
    date = models.DateField()



