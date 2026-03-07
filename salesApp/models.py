from django.db import models
from businessApp.models import BusinessBranch, Business
from warehouseApp.models import Product

# Create your models here.

# for retail and wholesale business ================================================================================
class RetailAndWholesale(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    quantityInStock = models.FloatField(default=0.0) # in pieces, kg, litres, etc
    reorderLevel = models.FloatField(default=0.0) # in pieces, kg, litres, etc. when stock reaches this level, reorder is needed
    partCanBeSold = models.BooleanField(default=True) # whether product can be sold in parts or not
    isVisibleOnline = models.BooleanField(default=True)
    enableOnlineOrder = models.BooleanField(default=False)
    minimumOrder = models.FloatField(default=1)     
    currentCostPriceRef = models.ForeignKey('CurrentCostAndPrice', on_delete=models.DO_NOTHING)
    measureRef = models.ForeignKey('MeasuringUnits', on_delete=models.DO_NOTHING, null=True)
    quantityRef = models.ForeignKey('Quantities', on_delete=models.DO_NOTHING, null=True)
    discountRef = models.ForeignKey('DiscountRate', on_delete=models.DO_NOTHING, null=True)
    returnPeriod = models.IntegerField(default=0) # period in days a customer can return the product


# discount on individual product under individual branch
class DiscountRate(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    productRef = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount = models.FloatField(default=0.00)
    discountSwaper = models.FloatField(default=0.00) # this will inital store the discount and swap it later
    addedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING, related_name='individualDiscount')
    startFrom = models.DateTimeField(null=True)
    endAt = models.DateTimeField(null=True)
    isActive = models.BooleanField(default=False)
    

# transactions on hold
class TransactionIDs(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    userRef = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    transactionID = models.CharField(max_length=50, unique=True)
    isSelcted = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)


# determine the selling and keeping units
class MeasuringUnits(models.Model):
    stockedUnit = models.CharField(max_length=30) # the unit at which the item is store in inventory
    soldUnit = models.CharField(max_length=30) # the unit at which item is sold to te customer


class CustomMeasuringUnit(models.Model):
    bussRef = models.ForeignKey(Business, on_delete=models.CASCADE)
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE, null=True)
    unit = models.CharField(max_length=50)
    unityType = models.CharField(max_length=15) # For Stock Keeping, For Selling, Both


# measuring pack qty against unitQty
class Quantities(models.Model):
    qtyPerPack = models.FloatField(default=1.0)
    packQty = models.FloatField(default=0.0)
    uintQty = models.FloatField(default=0.0)


# telly the quantities in and out of the product
class RetailWholesalesTally(models.Model):
    retailAndWholesaleRef = models.ForeignKey(RetailAndWholesale, on_delete=models.CASCADE)
    transactionType = models.CharField(default='In')  # Out, In
    quantity = models.FloatField(default=0.0)
    balance = models.FloatField(default=0.0)
    unitQuantity = models.FloatField(default=0.0)
    uintBalance = models.FloatField(default=0.0)
    narration = models.CharField(max_length=500) 
    date = models.DateField()
    transactionBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# stock adjustment =============================================================================
class StockAdjustment(models.Model):
    retailAndWholesaleRef = models.ForeignKey(RetailAndWholesale, on_delete=models.CASCADE)
    adjustmentType = models.CharField(max_length=15, default='Wrong Entry') # Wrong Entry, Expired, Damaged, Lost
    transactionType = models.CharField(max_length=3, default='Out') # Out, In
    quantity = models.FloatField(default=0.0)
    oldStock = models.FloatField(default=0.00)
    newStock = models.FloatField(default=0.00)
    oldStockUnit = models.FloatField(default=0.00)
    newStockUnit = models.FloatField(default=0.00)
    narration = models.CharField(max_length=100)
    transactionBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    date = models.DateTimeField()


# suppliers for retail and wholesale products
class ProductSuppliers(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    supplierName = models.CharField(max_length=100)
    supplierContact = models.CharField(max_length=100)
    supplierAddress = models.CharField(max_length=200)
    amountOwed = models.FloatField(default=0.00)


# records of quantities supplied by each supplier
class SupplyQuantityRecords(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    supplierRef = models.ForeignKey(ProductSuppliers, on_delete=models.CASCADE) 
    transactionID = models.CharField(max_length=50, null=True)    
    transactionType = models.CharField(max_length=15, default='Supply') # Supply, Repayment, Reversed Repayment, Reversed Supply
    receiptNumber = models.CharField(max_length=50, null=True)    
    totalCost = models.FloatField(default=0.00)
    amountPaid = models.FloatField(default=0.00)
    amountOwe = models.FloatField(default=0.00)
    Balance = models.FloatField(default=0.00)
    supplyDate = models.DateField()
    receivedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    narration = models.CharField(max_length=500, default='')
    isDisabled = models.BooleanField(default=False)
    def setAmountOwe(self):
        self.amountOwe = float(self.totalCost) - float(self.amountPaid)
        return self.amountOwe        


# individual items supplied
class IndividualItemsSupplied(models.Model):
    productRef = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    supplyRef = models.ForeignKey(SupplyQuantityRecords, on_delete=models.CASCADE)
    qty = models.FloatField(default=0)
    unityCost = models.FloatField(default=0.00)
    totalCost = models.FloatField(default=0.00)


# record temparily the quantity supplied 
class TempSupplyQuantity(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    supplierRef = models.ForeignKey(ProductSuppliers, on_delete=models.CASCADE)
    userRef = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)  
    productRef = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    qty = models.FloatField(default=0)
    amountPaid = models.FloatField(default=0.00)
    amountOwe = models.FloatField(default=0.00)
    unityCost = models.FloatField(default=0.00)
    totalCost = models.FloatField(default=0.00)


# current cost and price of retail and wholesale products
class CurrentCostAndPrice(models.Model):
    costPrice = models.FloatField(default=0.00)
    unitCostPrice = models.FloatField(default=0.00)
    sellingPrice = models.FloatField(default=0.00)
    unitSellingPrice = models.FloatField(default=0.00) 


# Selling price and cost history
class PriceHistory(models.Model):
    retailAndWholesaleRef = models.ForeignKey(RetailAndWholesale, on_delete=models.CASCADE)
    prices = models.FloatField(default=0.00)
    costs = models.FloatField(default=0.00)
    changeDate = models.DateField()


# customers for retail and wholesale products
class RetailAndWholesaleCustomers(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    customerName = models.CharField(max_length=100)
    customerContact = models.CharField(max_length=100)
    customerAddress = models.CharField(max_length=200, null=True)
    totalAmountOwed = models.FloatField(default=0.00)
    lastTransactionDate = models.DateField(null=True)


# customer owing details
class CustomerOwingDetails(models.Model):
    customerRef = models.ForeignKey(RetailAndWholesaleCustomers, on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=50)
    operationType = models.CharField(max_length=10) # Paid, Owed
    amount = models.FloatField(default=0.00)
    balance = models.FloatField(default=0.00)
    date = models.DateTimeField()


# customer payment details in a transaction
class CustomerPayments(models.Model):
    salesRef = models.ForeignKey('SalesRecords', on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=30)
    amountOwe = models.FloatField(default=0.0) 
    amountPaid = models.FloatField(default=0.0) # this is current amount paid 
    balance = models.FloatField(default=0.0) 
    date = models.DateTimeField(null=True, blank=True)
    paidBy = models.CharField(max_length=50, null=True)
    paymentBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)


# items purchased in each customer transaction
class CustomerItemsPurchased(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=30) 
    productName = models.CharField(max_length=30)
    productCode = models.CharField(max_length=15)
    measureUnit = models.CharField(max_length=15) # in pieces, kg, litres, etc
    quantity = models.FloatField()
    quantityReturned = models.FloatField(default=0) # what the customer has returned
    pricePerUnit = models.FloatField(default=0.0) 
    costPerUnit = models.FloatField(default=0.0) 
    promotionRate = models.FloatField(default=0.00)
    unitDiscount = models.FloatField(default=0.00)
    discount = models.FloatField(default=0.00)
    totalPrice = models.FloatField(default=0.0)
    date = models.DateField(null=True, auto_now_add=True) 


# return purchase items
class ReturnedProductsRecord(models.Model):
    salesRef = models.ForeignKey('SalesRecords', on_delete=models.CASCADE) 
    productRef = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField()
    pricePerUnit = models.FloatField(default=0.0) 
    totalPrice = models.FloatField(default=0.0)
    date = models.DateField(null=True, auto_now_add=True)
    returnedBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    reason = models.CharField(max_length=300)

# total amount to be returned to customer from return items of a particular sales
class ReturnAmountToCustomer(models.Model):
    salesRef = models.ForeignKey('SalesRecords', on_delete=models.CASCADE)
    amountToPay = models.FloatField(default=0.00)
    status = models.CharField(max_length=20, default='Pending') #Pending, Refunded


# store all transactions made by a customer
class AllCustomerTransactions(models.Model):
    customerRef = models.ForeignKey(RetailAndWholesaleCustomers, on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=50) 
    paymentTerms = models.CharField(max_length=30)   
    transactionType = models.CharField(max_length=15, default="Purchased") # Repayment, Purchased  
    transactionDate = models.DateField()
    transactionBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    totalPrice = models.FloatField(default=0.0) 
    discount = models.FloatField(default=0.0)
    currentPayment = models.FloatField(default=0.0)
    amountTopay = models.FloatField(default=0.0)
    amountPaid = models.FloatField(default=0.0)
    amountOwe = models.FloatField(default=0.0)
    oweBalance = models.FloatField(default=0.0)
    narration = models.CharField(max_length=500)

# payment agreement
class PaymentAgreement(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=30)
    paymentTerm = models.CharField(max_length=20)
    numberDays = models.IntegerField() #number of days to complete the payment 
    daysBeforeNextPayment = models.IntegerField() # number of days before next payment is made
    agreementLetter = models.CharField(max_length=500)
    nextPaymentDate = models.DateField()
    nextPaymentAmount = models.FloatField(default=0.00)
    totalAmount = models.FloatField(default=0.00)
    paneltyRatePerBreach = models.FloatField(default=0.00) # in percentage, 
    totalPaneltyCharges = models.FloatField(default=0.00)


# payment agreement details
class PaymentAgreementDetails(models.Model):
    payAgreemtRef = models.ForeignKey(PaymentAgreement, on_delete=models.CASCADE)
    dateToPay = models.DateField()
    paidOn = models.DateField()
    panelty = models.FloatField()
    amountPaid = models.FloatField(default=0.00)
    amountRemain = models.FloatField(default=0.00)   


#confirm code for the agreement
class AgreementConfirmationCode(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=30)
    code = models.CharField(max_length=10)
    customerContact = models.CharField(max_length=100)


# exclude some days in the payment agreement
class ExcludeDays(models.Model):
    transactionID = models.CharField(max_length=30)
    days = models.CharField(max_length=15)


#Advance Payment Items
class AdvancePaymentItems(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    customerRef = models.ForeignKey(RetailAndWholesaleCustomers, on_delete=models.CASCADE, null=True)
    productRef = models.ForeignKey(Product, on_delete=models.CASCADE)
    payAgreemtRef = models.ForeignKey(PaymentAgreement, on_delete=models.CASCADE)
    quatity = models.FloatField()
    pricePerUnit = models.FloatField()
    costPerUnit = models.FloatField()
    totalPrice = models.FloatField()


#advance payment item details
class AdvancePaymentItemsDetails(models.Model):
    advanceItemRef = models.ForeignKey(AdvancePaymentItems, on_delete=models.CASCADE)
    operationType = models.CharField(max_length=15, default='Collected') # Collected, Added
    quantity = models.FloatField()
    balace = models.FloatField()
    date = models.DateTimeField()
    receiverName = models.CharField(max_length=50)
    receiverTel = models.CharField(max_length=21)
    

# set all payment date of a particular payment agreement
class DatesForPayments(models.Model):
    payAgreemtRef = models.ForeignKey(PaymentAgreement, on_delete=models.CASCADE)
    date = models.DateField()
    penalty = models.FloatField(default=0.00) # penalty when contract is breached for this date
    day = models.CharField(max_length=15, null=True)


# temporary purchase details
class TemporalPurchaseDetails(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=30)
    totalPrice = models.FloatField(default=0.00) 
    amountToPay = models.FloatField(default=0.00) 
    discount = models.FloatField(default=0.00)
    discountRate = models.FloatField(default=0.00)    


# Sales records 
class SalesRecords(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    transactionID = models.CharField(max_length=30)
    paymentTerms = models.CharField(max_length=30, null=True)
    customerRef = models.ForeignKey(RetailAndWholesaleCustomers, on_delete=models.CASCADE, null=True)    
    customerName = models.CharField(max_length=50, null=True)
    customerTel= models.CharField(max_length=20, null=True)
    totalAmount = models.FloatField(default=0.0) 
    discount = models.FloatField(default=0.0) 
    amountToPay = models.FloatField(default=0.0) 
    amountPaid = models.FloatField(default=0.0) 
    amountOwe = models.FloatField(default=0.0) 
    amountReturned = models.FloatField(default=0.0)
    transactionDate = models.DateField()
    transactionBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    transactionIsConfirm = models.BooleanField(default=False)


# incident reports related to retail and wholesale business
class RetailAndWholesaleIncidentReports(models.Model):  
    retailAndWholesaleRef = models.ForeignKey(RetailAndWholesale, on_delete=models.CASCADE)
    reportTitle = models.CharField(max_length=100)
    reportDetails = models.CharField(max_length=300)
    date = models.DateField()


# this store items added to cart temporary
class AddToCart(models.Model):
    transactionID = models.CharField(max_length=30)
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    transactionBy = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    productRef = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0.0)
    pricePerItem = models.FloatField(default=0.00) 
    totalPrice = models.FloatField(default=0.00) 
    discount = models.FloatField(default=0.00)


# cash on hand
class CashOnhand(models.Model):
    branchRef = models.ForeignKey(BusinessBranch, on_delete=models.CASCADE)
    userRef = models.ForeignKey('usersApp.UserRef', on_delete=models.DO_NOTHING)
    cash = models.FloatField(default=0.00)
    totalTransaction = models.IntegerField(default=0) 
    date = models.DateField()

    
