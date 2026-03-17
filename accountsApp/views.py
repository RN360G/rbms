from urllib import request
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from salesApp.models import CashOnhand
from usersApp.models import UserRef
from accountsApp.models import OperationExpenses, Asset, Liability, Equity, Accounts, AccountTransaction, CashDenominations, TransferFundsRecord, OversAndShortages, OversAndShortagesRecord, SuspenseAccount, ShortagePaymentRecord, OverWithdrawalRecord, OnlineAccounts
from loginAndOutApp.views import loginSessions
from salesApp.models import CustomerItemsPurchased, StockAdjustment
import datetime as dt
from django.db.transaction import atomic
from django.db.models import Q, Sum, ExpressionWrapper, FloatField, Value, F
import random as rd
from django.contrib import messages
from businessApp.models import BusinessBranch, Business
from django.views.decorators.http import require_http_methods
from loginAndOutApp.views import dashboardMenuAccess
from usersApp.views import activityLogs, haveAccess

# Create your views here.

class AccountsView(generic.View):
    def get(self, request, type):
        dashboardMenuAccess(request)
        access = {
              '4':haveAccess(request, '4'),              
              '400':haveAccess(request, '400'), 
              '401':haveAccess(request, '401'), 
              '402':haveAccess(request, '402'), 
              '403':haveAccess(request, '403'), 
              '404':haveAccess(request, '404'),
              '405':haveAccess(request, '405'),

              '5':haveAccess(request, '5'),
              '500':haveAccess(request, '500'), 
              '501':haveAccess(request, '501'),
              '502':haveAccess(request, '502'),
            }
        if type == 'business':
            if not haveAccess(request, '5'):
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'You do not have access to business account management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
                return render(request, 'user/state.html')  
            # get all accounts
            acc = Accounts.objects.filter(Q(busRef=loginSessions(request, 'business'))).order_by('-accountBalance')
            suspenseInterbranch = SuspenseAccount.objects.filter(Q(toAccountRef__accountNumber=loginSessions(request, 'business').busID) & Q(option='interBranch'))
            businessAccountBal = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'business').busID)).accountBalance
            toAccounts = Accounts.objects.filter(Q(busRef=loginSessions(request, 'business'))).exclude(Q(accountNumber=loginSessions(request, 'business').busID) | Q(accountType='Staff Account'))

            totalAmountTobeAuthorize = suspenseInterbranch.aggregate(Sum('amount'))['amount__sum']

            #total shortage base on branch
            branchShortages = OversAndShortages.objects.values('branchRef__branchID', 'branchRef__branchName').annotate(shortageSum=Sum('shortageAmount'), overSum=Sum('overAmount')).filter(Q(busRef=loginSessions(request, 'business')))

            totalShortages = branchShortages.aggregate(Sum('shortageAmount'))['shortageAmount__sum']
            totalOvers = branchShortages.aggregate(Sum('overAmount'))['overAmount__sum']
            return render(request, 'accounts/accounts.html', {'accounts': acc, 'uAccess':access,'suspenesAccountFunds': suspenseInterbranch, 'totalAmt': totalAmountTobeAuthorize, 'toAccounts': toAccounts, 'businessAccountBal': businessAccountBal, 'branchShortages': branchShortages, 'totalShortages': totalShortages, 'totalOvers': totalOvers})
        else:
            if not haveAccess(request, '4'):
                messages.set_level(request, messages.WARNING)
                messages.warning(request, {'message': 'You do not have access to branch account management page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
                return render(request, 'user/state.html')
            acc = Accounts.objects.filter(Q(busRef=loginSessions(request, 'business')) & Q(branchRef=loginSessions(request, 'branch')))
            transactions = AccountTransaction.objects.filter(Q(accountRef__accountNumber=loginSessions(request, 'branch').branchID)).order_by('-id')
            toAccounts = Accounts.objects.filter(Q(busRef=loginSessions(request, 'business'))).exclude(Q(accountNumber=loginSessions(request, 'branch').branchID) | Q(accountType='Staff Account'))
            branchAccountBal = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'branch').branchID)).accountBalance            
            suspenseCashOnHand = SuspenseAccount.objects.filter(Q(toBranch=loginSessions(request, 'branch')))
            suspenseInterbranch = SuspenseAccount.objects.filter(Q(fromBranch=loginSessions(request, 'branch')) & Q(option='interBranch'))
            shortages = OversAndShortages.objects.filter(Q(branchRef=loginSessions(request, 'branch')))

            totalShortages = shortages.aggregate(Sum('shortageAmount'))['shortageAmount__sum']
            totalOver = shortages.aggregate(Sum('overAmount'))['overAmount__sum']

            totalAmountTobeAuthorize = suspenseCashOnHand.aggregate(Sum('amount'))['amount__sum']

            onlineAccounts = OnlineAccounts.objects.filter(branchRef=loginSessions(request, 'branch'))
            return render(request, 'accounts/branchAccount.html', {'accounts': acc, 'uAccess':access, 'branchAccountTransactions': transactions, 'toAccounts': toAccounts, 'branchAccountBal': branchAccountBal, 'suspenesAccountFunds': suspenseCashOnHand, 'totalAmt': totalAmountTobeAuthorize, 'suspenseInterbranch': suspenseInterbranch, 'shortages': shortages, 'totalShortages': totalShortages, 'totalOvers': totalOver, 'onlineAccounts': onlineAccounts})
    
    def post(self, request, type):
        return HttpResponse()
    
    # Get branch account transactions
    def branchAccountTransactions(request, pk):
        dashboardMenuAccess(request)
        account = Accounts.objects.get(Q(id=pk))
        transactions = AccountTransaction.objects.filter(Q(accountRef__accountNumber=account.accountNumber)).order_by('-id')
        return render(request, 'accounts/branchAccountTransactions.html', {'account': account, 'transactions': transactions})
    
    # Get business account transactions
    def businessAccountTransactions(request, pk):
        dashboardMenuAccess(request)
        account = Accounts.objects.get(Q(id=pk))
        transactions = AccountTransaction.objects.filter(Q(accountRef__accountNumber=account.accountNumber)).order_by('-id')
        return render(request, 'accounts/businesAccountTransactions.html', {'account': account, 'transactions': transactions})

    # deposit or withdraw fund from account
    def depositAndWithdrawal(request):
        transactionType = request.POST.get('transactionType')
        amount = request.POST.get('amount')
        narration = request.POST.get('narration')
        with atomic():
            acc = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'business').busID))
            if transactionType == 'Deposit':
                # deposit fund
                accountTransactions(request, acc.accountNumber, 'Credit', amount, narration)
            elif transactionType == 'Withdrawal':
                # withdraw fund
                if float(amount) > float(acc.accountBalance):
                    messages.set_level(request, messages.ERROR)
                    messages.error(request, {'message': 'Account balance is less than withdrawal amount', 'title': 'Low Account Balance'}, extra_tags='accountBalanceIslessThanWithdrawalAmount')
                    return render(request, 'accounts/state.html')
                else:
                    accountTransactions(request, acc.accountNumber, 'Debit', amount, narration)
            return redirect('accounts', type='business')     
        
    # deposit and withdrawal from branch account    
    def depositAndWithdrawalFromBranchAcc(request):
        with atomic():
            transactionType = request.POST.get('transactionType')
            amount = request.POST.get('amount')
            narration = request.POST.get('narration')
            with atomic():
                acc = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'branch').branchID))
                if transactionType == 'Deposit':
                    # deposit fund
                    accountTransactions(request, acc.accountNumber, 'Credit', amount, narration)
                elif transactionType == 'Withdrawal':
                    # withdraw fund
                    if float(amount) > float(acc.accountBalance):
                        messages.set_level(request, messages.ERROR)
                        messages.error(request, {'message': 'Account balance is less than withdrawal amount', 'title': 'Low Account Balance'}, extra_tags='accountBalanceIslessThanWithdrawalAmountFromBranchAcc')
                        return render(request, 'accounts/state.html')
                    else:
                        accountTransactions(request, acc.accountNumber, 'Debit', amount, narration)
            return redirect('accounts', type='branch') 


        
# expenses view
class ExpensesView(generic.View):
    def get(self, request):
        if not haveAccess(request, '13'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to expenses page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        dashboardMenuAccess(request)
        exp = OperationExpenses.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(enteredBy=loginSessions(request, 'user'))).order_by('-id')
        account = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'branch').branchID))
        return render(request, 'accounts/expenses.html', {'expenses': exp, 'account': account})

    def post(self, request):
        if not haveAccess(request, '13'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to expenses page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        # Process form data here
        expenesType = request.POST.get('expenesType')
        amount = request.POST.get('amount')
        narration = request.POST.get('narration')
        with atomic():
            acc = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'branch').branchID))
            if float(amount) > float(acc.accountBalance):
                messages.set_level(request, messages.ERROR)
                messages.error(request, {'message': 'Account balance is less than expense', 'title': 'Low Account Balance'}, extra_tags='accountBalanceIslessThanExpense')
                return render(request, 'accounts/state.html')
            else:
                exp = OperationExpenses()
                exp.busRef = loginSessions(request, 'business') 
                exp.branchRef = loginSessions(request, 'branch')
                exp.expenseType = expenesType
                exp.amount = amount
                exp.description = narration
                exp.dateIncurred = dt.datetime.now()
                exp.enteredBy = loginSessions(request, 'user')
                exp.save()
                
                # add this transaction to the account
                accountTransactions(request, loginSessions(request, 'branch').branchID, 'Debit', amount, narration)
                return redirect('expenses')         
    
    def deleteExpense(request, pk):
        if not haveAccess(request, '13'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to expenses page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        exp = OperationExpenses.objects.get(Q(id=pk))
        accountTransactions(request, loginSessions(request, 'branch').branchID, 'Credit', exp.amount, f'Reversed Expenses performed on {exp.dateIncurred}')
        exp.delete()
        return  redirect('expenses')
    

# account transactions
def accountTransactions(request, accountNumber, transactiontType, amount, narration):
    with atomic():
        account = Accounts.objects.get(Q(accountNumber=accountNumber))

        if transactiontType == 'Debit':
            account.accountBalance -= float(amount)
        elif transactiontType == 'Credit':
            account.accountBalance += float(amount)
        else:
            pass
        account.save()
        accTrans = AccountTransaction()
        accTrans.accountRef = account
        accTrans.transactionType = transactiontType
        accTrans.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().minute}{dt.datetime.now().second}{rd.randrange(1000,9999)}"
        accTrans.amount = amount
        accTrans.balance = account.accountBalance
        accTrans.narration = narration
        accTrans.date = dt.datetime.now()
        accTrans.enteredBy = loginSessions(request, 'user')
        accTrans.save()


class CashAnalysisView(generic.View):
    def get(self, request):
        if not haveAccess(request, '7'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to cash analysis page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        dashboardMenuAccess(request)
        checkCashOnHand = CashOnhand.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
        if not checkCashOnHand.exists():
            return redirect('dashboard')
        elif checkCashOnHand.exists() and float(checkCashOnHand[0].cash) <= 0.00:
            return redirect('dashboard')
        else:
            cashStatus = 0.00
            status = "Cash not transfered"
            cashAnalysis = CashDenominations.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(addedBy=loginSessions(request, 'user')))
            if cashAnalysis.exists():
                cashAnalysis = cashAnalysis.last()
                cashStatus = float("%.2f" % float(cashAnalysis.CashOnhandRef.cash - cashAnalysis.totalCash))  
                status = cashAnalysis.status          
            else:
                cashAnalysis = None

            if cashStatus > 0:
                cashStatus = cashStatus
            elif cashStatus < 0:
                cashStatus = cashStatus * -1  
            return render(request, 'accounts/cashanalysis.html', {'cashAnalysis': cashAnalysis, 'cashStatus': cashStatus, 'status': status})

    def post(self, request):
        if not haveAccess(request, '7'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to cash analysis page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        cash200 = request.POST.get('cash200')
        cash100 = request.POST.get('cash100')
        cash50 = request.POST.get('cash50')
        cash20 = request.POST.get('cash20')
        cash10 = request.POST.get('cash10')
        cash5 = request.POST.get('cash5')
        cash2 = request.POST.get('cash2')
        cash1 = request.POST.get('cash1')
        coins50pesewas = request.POST.get('cash50P')
        coins20pesewas = request.POST.get('cash20P')
        coins10pesewas = request.POST.get('cash10P')
        coins5pesewas = request.POST.get('cash5P')
        coins1pesewa = request.POST.get('cash1P')

        c200 = float(cash200) * 200
        c100 = float(cash100) * 100
        c50 = float(cash50) * 50
        c20 = float(cash20) * 20
        c10 = float(cash10) * 10
        c5 = float(cash5) * 5
        c2 = float(cash2) * 2
        c1 = float(cash1) * 1
        p50 = float(coins50pesewas) * 0.50
        p20 = float(coins20pesewas) * 0.20
        p10 = float(coins10pesewas) * 0.10
        p5 = float(coins5pesewas) * 0.05
        p1 = float(coins1pesewa) * 0.01
        totalCash = c200 + c100 + c50 + c20 + c10 + c5 + c2 + c1 + p50 + p20 + p10 + p5 + p1
        with atomic():
            cashDenom = CashDenominations.objects.filter(Q(branchRef=loginSessions(request, 'branch')) & Q(addedBy=loginSessions(request, 'user')))
            cashOnhand = CashOnhand.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
            if cashDenom.exists():
                cashDenom = cashDenom.last()
                cashDenom.cash200 = int(cash200)
                cashDenom.cash100 = int(cash100)
                cashDenom.cash50 = int(cash50)
                cashDenom.cash20 = int(cash20)
                cashDenom.cash10 = int(cash10)
                cashDenom.cash5 = int(cash5)
                cashDenom.cash2 = int(cash2)
                cashDenom.cash1 = int(cash1)
                cashDenom.coins50pesewas =  int(coins50pesewas)
                cashDenom.coins20pesewas = int(coins20pesewas)
                cashDenom.coins10pesewas = int(coins10pesewas)
                cashDenom.coins5pesewas = int(coins5pesewas)
                cashDenom.coins1pesewa = int(coins1pesewa)

                cashDenom.cash200Total = float(c200)
                cashDenom.cash100Total = float(c100)
                cashDenom.cash50Total = float(c50)
                cashDenom.cash20Total = float(c20)
                cashDenom.cash10Total = float(c10)
                cashDenom.cash5Total = float(c5)
                cashDenom.cash2Total = float(c2)
                cashDenom.cash1Total = float(c1)
                cashDenom.coins50pesewasTotal = float(p50)
                cashDenom.coins20pesewasTotal = float(p20)
                cashDenom.coins10pesewasTotal = float(p10)
                cashDenom.coins5pesewasTotal = float(p5)
                cashDenom.coins1pesewaTotal = float(p1)               
                cashDenom.save()
            else:
                cashDenom = CashDenominations()
                cashDenom.busRef = loginSessions(request, 'business')
                cashDenom.branchRef = loginSessions(request, 'branch')
                cashDenom.addedBy = loginSessions(request, 'user')
                cashDenom.cash200 = int(cash200)
                cashDenom.cash100 = int(cash100)
                cashDenom.cash50 = int(cash50)
                cashDenom.cash20 = int(cash20)
                cashDenom.cash10 = int(cash10)
                cashDenom.cash5 = int(cash5)
                cashDenom.cash2 = int(cash2)
                cashDenom.cash1 = int(cash1)
                cashDenom.coins50pesewas =  int(coins50pesewas)
                cashDenom.coins20pesewas = int(coins20pesewas)
                cashDenom.coins10pesewas = int(coins10pesewas)
                cashDenom.coins5pesewas = int(coins5pesewas)
                cashDenom.coins1pesewa = int(coins1pesewa)

                cashDenom.cash200Total = float(c200)
                cashDenom.cash100Total = float(c100)
                cashDenom.cash50Total = float(c50)
                cashDenom.cash20Total = float(c20)
                cashDenom.cash10Total = float(c10)
                cashDenom.cash5Total = float(c5)
                cashDenom.cash2Total = float(c2)
                cashDenom.cash1Total = float(c1)
                cashDenom.coins50pesewasTotal = float(p50)
                cashDenom.coins20pesewasTotal = float(p20)
                cashDenom.coins10pesewasTotal = float(p10)
                cashDenom.coins5pesewasTotal = float(p5)
                cashDenom.coins1pesewaTotal = float(p1) 

            cashDenom.totalCash = totalCash
            cashDenom.CashOnhandRef = cashOnhand            
            cashDenom.save()
        return HttpResponseRedirect('/accounts/cashanalysis/')
    
    

class SuspenseAccountView(generic.View):
    # suspense account for inter branch transfers
    def suspenseAccount(request, transactionType, froBranch, toBranch, fromAccountRef, toAccountRef, amount, overs, shortage, description):
        with atomic():
            if transactionType == 'cashOnHand':
                suspenseAcc = SuspenseAccount.objects.filter(Q(fromAccountRef__accountNumber=loginSessions(request, 'user').userID))
                if suspenseAcc.exists():
                    suspenseAcc = suspenseAcc[0]
                    suspenseAcc.amount = amount
                    suspenseAcc.oversAmount = overs
                    suspenseAcc.shortageAmount = shortage                    
                    suspenseAcc.description = description
                    suspenseAcc.save()
                else:
                    suspenseAcc = SuspenseAccount()
                    suspenseAcc.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().minute}{dt.datetime.now().second}{rd.randrange(1000,9999)}"
                    suspenseAcc.busRef = loginSessions(request, 'business')
                    suspenseAcc.option = 'cashOnHand'
                    suspenseAcc.fromBranch = froBranch
                    suspenseAcc.toBranch = toBranch
                    suspenseAcc.fromAccountRef = fromAccountRef
                    suspenseAcc.toAccountRef = toAccountRef
                    suspenseAcc.amount = amount
                    suspenseAcc.oversAmount = overs
                    suspenseAcc.shortageAmount = shortage
                    suspenseAcc.description = description
                    suspenseAcc.date = dt.datetime.now()
                    suspenseAcc.enteredBy = loginSessions(request, 'user')
                    suspenseAcc.save()
            else:
                suspenseAcc = SuspenseAccount()
                suspenseAcc.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().minute}{dt.datetime.now().second}{rd.randrange(1000,9999)}"
                suspenseAcc.busRef = loginSessions(request, 'business')
                suspenseAcc.option = 'interBranch'
                suspenseAcc.fromBranch = froBranch
                suspenseAcc.toBranch = toBranch
                suspenseAcc.fromAccountRef = fromAccountRef
                suspenseAcc.toAccountRef = toAccountRef
                suspenseAcc.amount = amount
                suspenseAcc.oversAmount = overs
                suspenseAcc.shortageAmount = shortage
                suspenseAcc.description = description
                suspenseAcc.date = dt.datetime.now()
                suspenseAcc.enteredBy = loginSessions(request, 'user')
                suspenseAcc.save()
    

    # transfer fund temporary to suspense account
    def transferToSuspenseAccount(request, opt):
        toAccount = None
        fromAccount = None
        fromBranch = None
        toBranch = None
        amount = 0.00
        overs = 0.00
        shortage = 0.00
        narration = None

        if opt == "cashOnHand":            
            cashOnhand = CashOnhand.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(userRef=loginSessions(request, 'user')))
            cashDenom = CashDenominations.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(addedBy=loginSessions(request, 'user')))
            amount = float(round(cashOnhand.cash, 2))
            difference = round(float(cashOnhand.cash) - float(cashDenom.totalCash), 2)

            cashDenom.status = "Fund Waiting for approval"
            cashDenom.save()

            cashOnH = round(cashOnhand.cash, 2)
            totalC = round(cashDenom.totalCash, 2)

            if difference < 0:
                difference = difference * -1
            toAccount = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'branch').branchID)) 
            fromAccount = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'user').userID))
            toBranch = loginSessions(request, 'branch')
            fromBranch = loginSessions(request, 'branch')            
            narration = f"Cash on hand from {fromAccount.accountName} ({fromAccount.accountNumber}) with an amount of {cashOnhand.cash}"
            if float(cashOnH) > float(totalC):
                shortage = difference  
                amount = amount-difference              
                narration = f"Cash on hand from {fromAccount.accountName} ({fromAccount.accountNumber}) with an amount of {amount} and shortage of {difference}"
            elif float(cashOnH) < float(totalC):
                amount = cashOnhand.cash
                overs = difference
                narration = f"Cash on hand from {fromAccount.accountName} ({fromAccount.accountNumber}) with an amount of {amount} and overs of {difference}"
                        
            SuspenseAccountView.suspenseAccount(request, 'cashOnHand', fromBranch, toBranch, fromAccount, toAccount, amount, overs, shortage, narration)
            #previous_page_url = request.META.get('HTTP_REFERER', '/')
            #return HttpResponseRedirect(previous_page_url)
            messages.set_level(request, messages.SUCCESS)
            messages.success(request, {'message': 'Fund transfer to suspense account successful. Ask the branch manager to authorize your transaction', 'title': 'Transfer Successful'}, extra_tags='fundTransferToSuspenseAccountSuccess')
            return render(request, 'accounts/state.html')
        elif opt == "interBranch":
            toAccountID = request.POST.get('toAccount')
            amount = request.POST.get('amount')
            narration = request.POST.get('narration')
            fromAccount = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'branch').branchID))
            toAccount = Accounts.objects.get(Q(accountNumber=toAccountID))
            fromBranch = loginSessions(request, 'branch')
            toBranch = toAccount.branchRef
            # process inter branch transfer to suspense account
            SuspenseAccountView.suspenseAccount(request, 'interBranch', fromBranch, toBranch, fromAccount, toAccount, amount, overs, shortage, narration)   
            messages.set_level(request, messages.SUCCESS)
            messages.success(request, {'message': 'Fund transfer to suspense account successful. Ask the destination account manager to authorize your transaction', 'title': 'Transfer Successful'}, extra_tags='fundTransferToSuspenseAccountSuccessInterBranch')
            return render(request, 'accounts/state.html')
        elif opt == "businessToBranch":
            toAccountID = request.POST.get('toAccount')
            amount = request.POST.get('amount')
            narration = request.POST.get('narration')
            fromAccount = Accounts.objects.get(Q(accountNumber=loginSessions(request, 'business').busID))
            toAccount = Accounts.objects.get(Q(accountNumber=toAccountID))
            fromBranch = loginSessions(request, 'branch')
            toBranch = toAccount.branchRef
            # process inter branch transfer to suspense account
            SuspenseAccountView.suspenseAccount(request, 'businessToBranch', fromBranch, toBranch, fromAccount, toAccount, amount, overs, shortage, narration)   
            messages.set_level(request, messages.SUCCESS)
            messages.success(request, {'message': 'Fund transfer to suspense account successful. Ask the destination account manager to authorize your transaction', 'title': 'Transfer Successful'}, extra_tags='fundTransferToSuspenseAccountSuccessFromBusinessToBranch')
            return render(request, 'accounts/state.html') 

    # authorize fund transfer
    def authorizeFundTransfer(request, transferType, pk, opt):
        suspenseAcc = SuspenseAccount.objects.get(Q(id=pk))

        # authorize cash on hand transfer
        if transferType == 'cashOnHand':
            user = UserRef.objects.get(Q(userID=suspenseAcc.fromAccountRef.accountNumber))
            branchAccount = Accounts.objects.get(Q(accountNumber=suspenseAcc.toAccountRef.accountNumber))
            fromAccount = Accounts.objects.get(Q(accountNumber=suspenseAcc.fromAccountRef.accountNumber))
            cashOnhand = CashOnhand.objects.get(Q(branchRef=suspenseAcc.fromBranch) & Q(userRef=user))
            cashDenom = CashDenominations.objects.get(Q(branchRef=loginSessions(request, 'branch')) & Q(addedBy__id=user.id))
            cashOnH = round(cashOnhand.cash, 2)
            totalC = round(cashDenom.totalCash, 2)
            amount = 0
            if opt == 'approve':
                with atomic():
                    if float(cashOnhand.cash) <= 0:
                        messages.set_level(request, messages.ERROR)
                        messages.error(request, {'message': 'No cash to be transfered', 'title': 'Transfer Failed'}, extra_tags='noCashOnHand')
                        return render(request, 'accounts/state.html')
                    else:
                        amount = totalC
                        # save overs and shortages
                        oversAndShortagesRecord = OversAndShortagesRecord()
                        cashDifference = round(float(cashOnhand.cash) - float(cashDenom.totalCash), 2)
                        if cashDifference < 0:
                            cashDifference = cashDifference * -1

                        oversAndShortages = OversAndShortages.objects.filter(Q(busRef=loginSessions(request, 'business')) & Q(branchRef=loginSessions(request, 'branch')) & Q(fromAccountRef=fromAccount))
                        if not oversAndShortages.exists():                            
                            oversAndShortages = OversAndShortages()
                            oversAndShortages.busRef = loginSessions(request, 'business')
                            oversAndShortages.branchRef = loginSessions(request, 'branch')
                            oversAndShortages.fromAccountRef = fromAccount
                            if cashOnH < totalC:
                                oversAndShortages.overAmount = float(cashDifference)
                                oversAndShortagesRecord.transactionType = 'Overs'
                                amount = round(float(cashOnhand.cash), 2)
                                oversAndShortages.save()
                            elif cashOnH > totalC:
                                oversAndShortages.shortageAmount = float(cashDifference)
                                oversAndShortagesRecord.transactionType = 'Shortage'
                                amount = float(totalC)
                                oversAndShortages.save()
                        else:
                            oversAndShortages = oversAndShortages[0]
                            if cashOnH < totalC:
                                oversAndShortages.overAmount += float(cashDifference)
                                oversAndShortages.save()
                                oversAndShortagesRecord.transactionType = 'Overs'
                                amount = round(float(cashOnhand.cash), 2)

                                # store over withdrawal record
                                overWithdrawalRecord = OverWithdrawalRecord.objects.filter(Q(accountRef=fromAccount))
                                bal = 0.00
                                if overWithdrawalRecord.exists():
                                    overWithdrawalRecord = overWithdrawalRecord.last()
                                    bal = float(overWithdrawalRecord.balance) + float(cashDifference) 
                                else:
                                    bal = float(cashDifference)
                                overWithdrawalRecord = OverWithdrawalRecord()
                                overWithdrawalRecord.busRef = loginSessions(request, 'business')
                                overWithdrawalRecord.branchRef = loginSessions(request, 'branch')  
                                overWithdrawalRecord.withdrawalType = "Credit" 
                                overWithdrawalRecord.narration = f"Overs deposit"    
                                overWithdrawalRecord.accountRef = fromAccount
                                overWithdrawalRecord.oversAndShortagesRef = oversAndShortages
                                overWithdrawalRecord.amount = float(cashDifference) 
                                overWithdrawalRecord.balance = bal
                                overWithdrawalRecord.date = dt.datetime.now()    
                                overWithdrawalRecord.enteredBy = loginSessions(request, 'user')
                                overWithdrawalRecord.save()
                            elif cashOnH > totalC:
                                oversAndShortages.shortageAmount += float(cashDifference)
                                oversAndShortages.save()
                                oversAndShortagesRecord.transactionType = 'Shortage' 
                                amount = float(totalC)
                        oversAndShortagesRecord.amount = cashDifference
                        oversAndShortagesRecord.date = dt.datetime.now()    
                        oversAndShortagesRecord.oversAndShortagesRef = oversAndShortages
                        oversAndShortagesRecord.save()
                        
                        # delete cash denominations and cash on hand                        
                        cashDenom.cash200 = 0
                        cashDenom.cash100 = 0
                        cashDenom.cash50 = 0
                        cashDenom.cash20 = 0
                        cashDenom.cash10 = 0
                        cashDenom.cash5 = 0
                        cashDenom.cash2 = 0
                        cashDenom.cash1 = 0
                        cashDenom.coins50pesewas =  0
                        cashDenom.coins20pesewas = 0
                        cashDenom.coins10pesewas = 0
                        cashDenom.coins5pesewas = 0
                        cashDenom.coins1pesewa = 0

                        cashDenom.cash200Total = 0
                        cashDenom.cash100Total = 0
                        cashDenom.cash50Total = 0
                        cashDenom.cash20Total = 0
                        cashDenom.cash10Total = 0
                        cashDenom.cash5Total = 0
                        cashDenom.cash2Total = 0
                        cashDenom.cash1Total = 0
                        cashDenom.coins50pesewasTotal = 0
                        cashDenom.coins20pesewasTotal = 0
                        cashDenom.coins10pesewasTotal = 0
                        cashDenom.coins5pesewasTotal = 0
                        cashDenom.coins1pesewaTotal = 0
                        cashDenom.totalCash = 0
                        cashDenom.save()
                        
                        # reset cash on hand
                        cashOnhand.cash = 0.00
                        cashOnhand.totalTransaction = 0
                        cashOnhand.save()
                    
                        # Debit staff account
                        accountTransactions(request, fromAccount.accountNumber, 'Debit', amount, f'Cash on hand transfer to branch account : {branchAccount.accountName} - {branchAccount.accountNumber}')                
                        # Credit to branch account
                        accountTransactions(request, branchAccount.accountNumber, 'Credit', amount, f'Cash on hand transfer from account : {fromAccount.accountName} - {fromAccount.accountNumber}')
                        
                        # Create transfer record
                        transferRecord = TransferFundsRecord()
                        transferRecord.transferType = 'Transfering'
                        transferRecord.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().minute}{dt.datetime.now().second}{rd.randrange(1000,9999)}"
                        transferRecord.fromAccountRef = fromAccount
                        transferRecord.toAccountRef = branchAccount
                        transferRecord.amount = amount
                        transferRecord.narration = f'Cash on hand transfer from account: {fromAccount.accountNumber} - {fromAccount.accountNumber} to branch account : {branchAccount.accountName} - {branchAccount.accountNumber}'
                        transferRecord.date = dt.datetime.now()
                        transferRecord.enteredBy = loginSessions(request, 'user')
                        transferRecord.save()
                    # delete suspense account record
                    suspenseAcc.delete()
                    return redirect('dashboard')
            elif opt == 'reject':
                with atomic():
                    # delete suspense account record
                    cashDenom.status = "Fund transfer rejected. Call branch manager for more info"
                    cashDenom.save()
                    suspenseAcc.delete()
                    previous_page_url = request.META.get('HTTP_REFERER', '/')
                    return HttpResponseRedirect(previous_page_url)
                
        # inter branch transfer authorization
        elif transferType == 'interBranch':
            with atomic():
                if opt == 'reject':
                    # delete suspense account record
                    suspenseAcc.delete()
                    previous_page_url = request.META.get('HTTP_REFERER', '/')
                    return HttpResponseRedirect(previous_page_url)
                else:
                    fromAccount = Accounts.objects.get(Q(accountNumber=suspenseAcc.fromAccountRef.accountNumber))
                    toAccount = Accounts.objects.get(Q(accountNumber=suspenseAcc.toAccountRef.accountNumber))
                    amount = suspenseAcc.amount
                    narration = suspenseAcc.description
                    if float(amount) > float(fromAccount.accountBalance):
                        messages.set_level(request, messages.ERROR)
                        messages.error(request, {'message': 'Insufficient funds in the source account', 'title': 'Transfer Failed'}, extra_tags='insufficientFunds')
                        return render(request, 'accounts/state.html')
                    else:
                        # Debit from source account
                        accountTransactions(request, fromAccount.accountNumber, 'Debit', amount, f'Transfer to {toAccount.accountName} - {toAccount.accountNumber}. Narration: {narration}')
                        
                        # Credit to destination account
                        accountTransactions(request, toAccount.accountNumber, 'Credit', amount, f'Transfer from {fromAccount.accountName} - {fromAccount.accountNumber}. Narration: {narration}')
                        transferRecord = TransferFundsRecord()
                        transferRecord.transferType = 'Transfering'
                        transferRecord.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().minute}{dt.datetime.now().second}{rd.randrange(1000,9999)}"
                        transferRecord.fromAccountRef = fromAccount
                        transferRecord.toAccountRef = toAccount
                        transferRecord.amount = amount
                        transferRecord.narration = narration    
                        transferRecord.date = dt.datetime.now()
                        transferRecord.enteredBy = loginSessions(request, 'user')
                        transferRecord.save()

                        # delete suspense account record
                        suspenseAcc.delete()
                        return redirect('accounts', type='business')
                    
        # business to branch transfer authorization                           
        elif transferType == 'businessToBranch':
            with atomic():
                if opt == 'reject':
                    # delete suspense account record
                    suspenseAcc.delete()
                    previous_page_url = request.META.get('HTTP_REFERER', '/')
                    return HttpResponseRedirect(previous_page_url)
                else:
                    fromAccount = Accounts.objects.get(Q(accountNumber=suspenseAcc.fromAccountRef.accountNumber))
                    toAccount = Accounts.objects.get(Q(accountNumber=suspenseAcc.toAccountRef.accountNumber))
                    amount = suspenseAcc.amount
                    narration = suspenseAcc.description
                    if float(amount) > float(fromAccount.accountBalance):
                        messages.set_level(request, messages.ERROR)
                        messages.error(request, {'message': 'Insufficient funds in the source account', 'title': 'Transfer Failed'}, extra_tags='insufficientFunds')
                        return render(request, 'accounts/state.html')
                    else:
                        # Debit from source account
                        accountTransactions(request, fromAccount.accountNumber, 'Debit', amount, f'Transfer to {toAccount.accountName} - {toAccount.accountNumber}. Narration: {narration}')
                        
                        # Credit to destination account
                        accountTransactions(request, toAccount.accountNumber, 'Credit', amount, f'Transfer from {fromAccount.accountName} - {fromAccount.accountNumber}. Narration: {narration}')
                        transferRecord = TransferFundsRecord()
                        transferRecord.transferType = 'Transfering'
                        transferRecord.transactionID = f"{dt.datetime.now().year}{dt.datetime.now().month}{dt.datetime.now().day}{dt.datetime.now().minute}{dt.datetime.now().second}{rd.randrange(1000,9999)}"
                        transferRecord.fromAccountRef = fromAccount
                        transferRecord.toAccountRef = toAccount
                        transferRecord.amount = amount
                        transferRecord.narration = narration    
                        transferRecord.date = dt.datetime.now()
                        transferRecord.enteredBy = loginSessions(request, 'user')
                        transferRecord.save()

                        # delete suspense account record
                        suspenseAcc.delete()
                        return redirect('accounts', type='business')  
                    

    # detete fund transfer from branch account
    def deleteFundTransferFromBranch(request, pk):
        suspense = SuspenseAccount.objects.get(Q(id=pk))        
        suspense.delete()
        return redirect('accounts', type='branch')
    
    # delete fund transfer from business account
    def deleteFundTransferFromBusiness(request, pk):
        suspense = SuspenseAccount.objects.get(Q(id=pk))        
        suspense.delete()
        return redirect('accounts', type='business')
    

# pay for shortages
class ShortagePayment(generic.View):
    def get(self, request, pk, payType):
        if not haveAccess(request, '400'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to cash shortage payment page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        dashboardMenuAccess(request)
        shortage = OversAndShortages.objects.get(Q(id=pk))
        shortagePaymentRecord = ShortagePaymentRecord.objects.filter(Q(oversAndShortagesRef=shortage)).order_by('-id')
        return render(request, 'accounts/shortagePayments.html', {'shortage': shortage, 'payType': payType, 'payments': shortagePaymentRecord})
    
    def post(self, request, pk, payType):  
        if not haveAccess(request, '400'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to cash shortage payment page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')       
        narration = request.POST.get('narration')
        amount = request.POST.get('amount')
        if payType == 'Pay':
            with atomic():
                shortage = OversAndShortages.objects.get(Q(id=pk))
                if float(amount) > float(shortage.shortageAmount):
                    messages.set_level(request, messages.ERROR)
                    messages.error(request, {'message': 'Payment amount exceeds shortage amount', 'title': 'Payment Error'}, extra_tags='shortagePaymentExceedsShortageAmount')
                    return render(request, 'accounts/state.html')
                else:
                    # process payment
                    shortage.shortageAmount -= float(amount)
                    shortage.save()
                    # add payment record
                    paymentRecord = ShortagePaymentRecord()
                    paymentRecord.oversAndShortagesRef = shortage
                    paymentRecord.paymentType = 'Made Payment'
                    paymentRecord.amount = amount
                    paymentRecord.balance = shortage.shortageAmount
                    paymentRecord.narration = narration
                    paymentRecord.date = dt.datetime.now()
                    paymentRecord.enteredBy = loginSessions(request, 'user')
                    paymentRecord.save()
                    # add transaction to account
                    accountTransactions(request, loginSessions(request, 'branch').branchID, 'Credit', amount, f'Shortage payment from Acc Num.: {shortage.fromAccountRef.accountNumber}. Narration: {narration}')
        else:
            with atomic():
                shortage = OversAndShortages.objects.get(Q(id=pk))
                if float(amount) > float(shortage.shortageAmount):
                    messages.set_level(request, messages.ERROR)
                    messages.error(request, {'message': 'Payment amount exceeds shortage amount', 'title': 'Payment Error'}, extra_tags='shortagePaymentExceedsShortageAmount')
                    return render(request, 'accounts/state.html')
                else:
                    # process payment
                    shortage.shortageAmount -= float(amount)
                    shortage.save()
                    # add payment record
                    paymentRecord = ShortagePaymentRecord()
                    paymentRecord.oversAndShortagesRef = shortage
                    paymentRecord.paymentType = 'Cleared Shortage'
                    paymentRecord.amount = amount
                    paymentRecord.balance = shortage.shortageAmount
                    paymentRecord.narration = narration
                    paymentRecord.date = dt.datetime.now()
                    paymentRecord.enteredBy = loginSessions(request, 'user')
                    paymentRecord.save()
        return redirect('accounts', type='branch')
    

# move overs to branch account after thorogh inverstigaion
class MoveOversToBranchAccount(generic.View):
    def get(self, request, pk):
        if not haveAccess(request, '401'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to cash overage movement page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        dashboardMenuAccess(request)
        over = OversAndShortages.objects.get(Q(id=pk))
        overWithdrawalRecord = OverWithdrawalRecord.objects.filter(Q(accountRef=over.fromAccountRef)).order_by('-id')
        return render(request, 'accounts/moveOver.html', {'overs': overWithdrawalRecord, 'totalOvers': over.overAmount})
    
    def post(self, request, pk):
        if not haveAccess(request, '401'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to cash overage movement page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html') 
        with atomic():
            narration = request.POST.get('narration')
            amount = request.POST.get('amount')
            over = OversAndShortages.objects.get(Q(id=pk))
            over.overAmount = float(over.overAmount) - float(amount)
            over.save()
            overRecord = OverWithdrawalRecord()
            overRecord.busRef = loginSessions(request, 'business')
            overRecord.branchRef = loginSessions(request, 'branch')
            overRecord.oversAndShortagesRef = over
            overRecord.withdrawalType = 'Debit'
            overRecord.accountRef = over.fromAccountRef
            overRecord.amount = round(float(amount), 2)
            overRecord.balance = over.overAmount
            overRecord.narration = narration
            overRecord.date = dt.datetime.now()
            overRecord.enteredBy = loginSessions(request, 'user')
            overRecord.save()
            accountTransactions(request, loginSessions(request, 'branch').branchID, 'Credit', amount, f'Deposit from overs account. : {over.fromAccountRef.accountNumber}. Narration: {narration}')
        return redirect('accounts', type='branch')


# pay roll 
class PayRoll(generic.View):
    def get(self, request):
        return render(request, 'accounts/payroll.html')
    
    def post(self, request):
        return HttpResponse()


# income statement
class IncomeStatementView(generic.View):
    def get(self, request):   
        if not haveAccess(request, '9'):
            messages.set_level(request, messages.WARNING)
            messages.warning(request, {'message': 'You do not have access to income statement page.', 'title': 'Access Denied'}, extra_tags='accessDenied')
            return render(request, 'user/state.html')   
        dashboardMenuAccess(request)   
        request.session.setdefault('incomeStatementStartDate', '')
        request.session.setdefault('incomeStatementEndDate', '')
        request.session.setdefault('incomeStatementType', '')
        request.session.setdefault('incomeStatementBranch', '')

        statementType = request.session['incomeStatementType']
        branchID = request.session['incomeStatementBranch']
        startDate = request.session['incomeStatementStartDate']
        endDate = request.session['incomeStatementEndDate']

        if startDate == '' or endDate == '' or statementType == '':
            if request.user_agent.is_mobile:
                return render(request, 'accounts/incomeStatementMobile.html')
            else:
                return render(request, 'accounts/incomeStatement.html')
        
        title = ''
        goods = None
        expenses = None
        overs = None
        shortages = None
        branch = None
        stockAdjustment = None
        if statementType == '100':
            goods = CustomerItemsPurchased.objects.values('productName').annotate(
                        totaltQty=Sum('quantity'),
                        totalSoldPrice = Sum('totalPrice'),
                        totalCostPrice=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=startDate) & Q(date__lte=endDate)))
                
            expenses = OperationExpenses.objects.annotate(
                        branchOperation = Sum(F('amount'), filter=Q(expenseType='Branch operations'), output_field=FloatField()),
                        transportation = Sum(F('amount'), filter=Q(expenseType='Transportation'), output_field=FloatField()),
                        waterBill = Sum(F('amount'), filter=Q(expenseType='Water Bill'), output_field=FloatField()),
                        salariesAndWages = Sum(F('amount'), filter=Q(expenseType='Salaries and Wages'), output_field=FloatField()),
                        electricityBill = Sum(F('amount'), filter=Q(expenseType='Electricity Bill'), output_field=FloatField()),
                        rent = Sum(F('amount'), filter=Q(expenseType='Rent'), output_field=FloatField()),
                        security = Sum(F('amount'), filter=Q(expenseType='Security'), output_field=FloatField()),
                        fuel = Sum(F('amount'), filter=Q(expenseType='Fuel'), output_field=FloatField()),
                        others = Sum(F('amount'), filter=Q(expenseType='Other Expenses'), output_field=FloatField()),
                        advertAndmarketing = Sum(F('amount'), filter=Q(expenseType='Advertising and Marketing'), output_field=FloatField()),
                        tax = Sum(F('amount'), filter=Q(expenseType='Tax'), output_field=FloatField()),
                        maintenance = Sum(F('amount'), filter=Q(expenseType='Maintenance and Repairs'), output_field=FloatField()),
                        allowance = Sum(F('amount'), filter=Q(expenseType='Allowance'), output_field=FloatField()),
                        mealsAndEntertainment = Sum(F('amount'), filter=Q(expenseType='Meals and Entertainment'), output_field=FloatField()),
                        internetFees = Sum(F('amount'), filter=Q(expenseType='Internet Fees'), output_field=FloatField())
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & (Q(dateIncurred__gte=startDate) & Q(dateIncurred__lte=endDate)))
            
            overs = OversAndShortagesRecord.objects.annotate(
                       overage = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(oversAndShortagesRef__branchRef__busRef=loginSessions(request, 'business')) & Q(transactionType='Overs') & (Q(date__gte=startDate) & Q(date__lte=endDate)))
            
            shortages = OversAndShortagesRecord.objects.annotate(
                      shortage = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(oversAndShortagesRef__branchRef__busRef=loginSessions(request, 'business')) & Q(transactionType='Shortage') & (Q(date__gte=startDate) & Q(date__lte=endDate))) 
            
            stockAdjustment = StockAdjustment.objects.annotate(
                   damages = Sum(F('quantity') * F('retailAndWholesaleRef__currentCostPriceRef__unitCostPrice'), filter=Q(adjustmentType='Damaged Products'), output_field=FloatField()),
                   expires = Sum(F('quantity') * F('retailAndWholesaleRef__currentCostPriceRef__unitCostPrice'), filter=Q(adjustmentType='Expired Products'), output_field=FloatField()),
                   lost = Sum(F('quantity') * F('retailAndWholesaleRef__currentCostPriceRef__unitCostPrice'), filter=Q(adjustmentType='Lost Products'), output_field=FloatField()),
                   foundLost = Sum(F('quantity') * F('retailAndWholesaleRef__currentCostPriceRef__unitCostPrice'), filter=Q(adjustmentType='Found Lost Products'), output_field=FloatField())
                ).filter(Q(retailAndWholesaleRef__branchRef__busRef=loginSessions(request, 'business')) & (Q(date__gte=startDate) & Q(date__lte=endDate)))
            
        elif statementType == '101':
            branch = BusinessBranch.objects.get(Q(branchID=loginSessions(request, 'branch').branchID) & Q(busRef=loginSessions(request, 'business')))

            goods = CustomerItemsPurchased.objects.annotate(
                   totaltQty=Sum('quantity'),
                   totalSoldPrice = Sum('totalPrice'),
                   totalCostPrice=Sum(ExpressionWrapper( F('costPerUnit') * F('quantity'), output_field=FloatField()))
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=branchID) & (Q(date__gte=startDate) & Q(date__lte=endDate)))
            
            expenses = OperationExpenses.objects.annotate(
                        branchOperation = Sum(F('amount'), filter=Q(expenseType='Branch operations'), output_field=FloatField()),
                        transportation = Sum(F('amount'), filter=Q(expenseType='Transportation'), output_field=FloatField()),
                        waterBill = Sum(F('amount'), filter=Q(expenseType='Water Bill'), output_field=FloatField()),
                        salariesAndWages = Sum(F('amount'), filter=Q(expenseType='Salaries and Wages'), output_field=FloatField()),
                        electricityBill = Sum(F('amount'), filter=Q(expenseType='Electricity Bill'), output_field=FloatField()),
                        rent = Sum(F('amount'), filter=Q(expenseType='Rent'), output_field=FloatField()),
                        security = Sum(F('amount'), filter=Q(expenseType='Security'), output_field=FloatField()),
                        fuel = Sum(F('amount'), filter=Q(expenseType='Fuel'), output_field=FloatField()),
                        others = Sum(F('amount'), filter=Q(expenseType='Other Expenses'), output_field=FloatField()),
                        advertAndmarketing = Sum(F('amount'), filter=Q(expenseType='Advertising and Marketing'), output_field=FloatField()),
                        tax = Sum(F('amount'), filter=Q(expenseType='Tax'), output_field=FloatField()),
                        maintenance = Sum(F('amount'), filter=Q(expenseType='Maintenance and Repairs'), output_field=FloatField()),
                        allowance = Sum(F('amount'), filter=Q(expenseType='Allowance'), output_field=FloatField()),
                        mealsAndEntertainment = Sum(F('amount'), filter=Q(expenseType='Meals and Entertainment'), output_field=FloatField()),
                        internetFees = Sum(F('amount'), filter=Q(expenseType='Internet Fees'), output_field=FloatField()),
                   ).filter(Q(branchRef__busRef=loginSessions(request, 'business')) & Q(branchRef__branchID=branchID) & (Q(dateIncurred__gte=startDate) & Q(dateIncurred__lte=endDate)))
            
            overs = OversAndShortagesRecord.objects.annotate(
                   overage = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(oversAndShortagesRef__branchRef__busRef=loginSessions(request, 'business')) & Q(oversAndShortagesRef__branchRef__branchID=branchID) & Q(transactionType='Overs') & (Q(date__gte=startDate) & Q(date__lte=endDate)))
            
            shortages = OversAndShortagesRecord.objects.annotate(
                   shortage = Sum(ExpressionWrapper(F('amount'), output_field=FloatField()))
                   ).filter(Q(oversAndShortagesRef__branchRef__busRef=loginSessions(request, 'business')) & Q(oversAndShortagesRef__branchRef__branchID=branchID) & Q(transactionType='Shortage') & (Q(date__gte=startDate) & Q(date__lte=endDate)))
            
            stockAdjustment = StockAdjustment.objects.annotate(
                   damages = Sum(F('quantity') * F('retailAndWholesaleRef__currentCostPriceRef__unitCostPrice'), filter=Q(adjustmentType='Damaged Products'), output_field=FloatField()),
                   expires = Sum(F('quantity') * F('retailAndWholesaleRef__currentCostPriceRef__unitCostPrice'), filter=Q(adjustmentType='Expired Products'), output_field=FloatField()),
                   lost = Sum(F('quantity') * F('retailAndWholesaleRef__currentCostPriceRef__unitCostPrice'), filter=Q(adjustmentType='Lost Products'), output_field=FloatField()),
                   foundLost = Sum(F('quantity') * F('retailAndWholesaleRef__currentCostPriceRef__unitCostPrice'), filter=Q(adjustmentType='Found Lost Products'), output_field=FloatField())
                ).filter(Q(retailAndWholesaleRef__branchRef__busRef=loginSessions(request, 'business')) & Q(retailAndWholesaleRef__branchRef__branchID=branchID) & (Q(date__gte=startDate) & Q(date__lte=endDate)))

        # revenue from goods sold================================================
        revenue = float(goods.aggregate(Sum('totalSoldPrice'))['totalSoldPrice__sum'] or 0)

        # cash overs and shortage ===============================================
        cashOver = overs.aggregate(Sum('overage'))['overage__sum']
        cashShort = shortages.aggregate(Sum('shortage'))['shortage__sum']
        
        # net income
        netIncome = float(revenue or 0) + float(cashOver or 0)

        # cost of goods sold==============================================================
        goodsSold = float(goods.aggregate(Sum('totalCostPrice'))['totalCostPrice__sum'] or 0)
        expires = float(stockAdjustment.aggregate(Sum('expires'))['expires__sum'] or 0)
        damages = float(stockAdjustment.aggregate(Sum('damages'))['damages__sum'] or 0)
        lost = float(stockAdjustment.aggregate(Sum('lost'))['lost__sum'] or 0)
        foundLost = float(stockAdjustment.aggregate(Sum('foundLost'))['foundLost__sum'] or 0) 
       
        
        lost = float(lost or 0) - float(foundLost or 0)
        lost = lost if lost > 0 else 0
        totalSoldCost = float(goodsSold) + float(expires or 0) + float(damages or 0) + float(lost or 0)

        # shortages =======================================================================
        cashShort = cashShort if cashShort else 0.00

        # expenses =======================================================================
        branchOpertion = float(expenses.aggregate(Sum('branchOperation'))['branchOperation__sum'] or 0)
        transportation = float(expenses.aggregate(Sum('transportation'))['transportation__sum'] or 0)
        waterBill = float(expenses.aggregate(Sum('waterBill'))['waterBill__sum'] or 0)
        salariesAndWages = float(expenses.aggregate(Sum('salariesAndWages'))['salariesAndWages__sum'] or 0)
        electricityBill = float(expenses.aggregate(Sum('electricityBill'))['electricityBill__sum'] or 0)
        rent = float(expenses.aggregate(Sum('rent'))['rent__sum'] or 0)
        security = float(expenses.aggregate(Sum('security'))['security__sum'] or 0)
        fuel = float(expenses.aggregate(Sum('fuel'))['fuel__sum'] or 0)
        others = float(expenses.aggregate(Sum('others'))['others__sum'] or 0)
        advertAndmarketing = float(expenses.aggregate(Sum('advertAndmarketing'))['advertAndmarketing__sum'] or 0)
        tax = float(expenses.aggregate(Sum('tax'))['tax__sum'] or 0)
        maintenance = float(expenses.aggregate(Sum('maintenance'))['maintenance__sum'] or 0)
        allowance = float(expenses.aggregate(Sum('allowance'))['allowance__sum'] or 0)
        mealsAndEntertainment = float(expenses.aggregate(Sum('mealsAndEntertainment'))['mealsAndEntertainment__sum'] or 0)
        internetFees = float(expenses.aggregate(Sum('internetFees'))['internetFees__sum'] or 0)
        totalExpenses = float(branchOpertion or 0) + float(transportation or 0) + float(waterBill or 0) + float(salariesAndWages or 0) + float(electricityBill or 0) + float(rent or 0) + float(security or 0) + float(fuel or 0) + float(others or 0) + float(advertAndmarketing or 0) + float(tax or 0) + float(maintenance or 0) + float(allowance or 0) + float(mealsAndEntertainment or 0) + float(internetFees or 0)
        
        # grose income ======================================================================================
        groseIncome = float(netIncome) - (float(totalSoldCost or 0) + float(totalExpenses or 0) + float(cashShort or 0))
        
        data = {
            'revenue': revenue,
            'overs': cashOver ,
            'shortages': cashShort,
            'netIncome': netIncome,
            'goodsSold': goodsSold,
            'expires': expires,
            'damages': damages,
            'lost': lost,
            'totalSoldCost': totalSoldCost,

            'branchOpertion': branchOpertion,
            'transportation': transportation,
            'waterBill': waterBill,
            'salariesAndWages': salariesAndWages,
            'electricityBill': electricityBill,
            'rent': rent,
            'security': security,
            'fuel': fuel,
            'others': others,
            'advertAndmarketing': advertAndmarketing,
            'tax': tax,
            'maintenance': maintenance,
            'allowance': allowance,
            'mealsAndEntertainment': mealsAndEntertainment,
            'internetFees': internetFees,
            'totalExpenses': totalExpenses,

            'groseIncome': groseIncome,

            'branch': branch,
            'business': loginSessions(request, 'business'),
            'startDate': startDate,
            'endDate': endDate,
            'statementType': statementType,
        }
        if request.user_agent.is_mobile:
            return render(request, 'accounts/incomeStatementMobile.html', data)
        else:
            return render(request, 'accounts/incomeStatement.html', data)
    
    
    def post(self, request):
        startDate = request.POST.get('fromDate')
        endDate = request.POST.get('toDate')
        statementType = request.POST.get('statementType')
        branchID = request.POST.get('branch')

        request.session['incomeStatementStartDate'] = startDate
        request.session['incomeStatementEndDate'] = endDate
        request.session['incomeStatementType'] = statementType
        request.session['incomeStatementBranch'] = branchID
        return redirect('salesIncomeState')
    

# Add online payment accounts
def addOnlinePaymentAccounts(request):
    with atomic():
        accountNumber = request.POST.get('accountNumber')
        accountName = request.POST.get('accountName')
        accountType = request.POST.get('accountType')
        
        db = OnlineAccounts()
        db.branchRef = loginSessions(request, 'branch')
        db.accountNumber = accountNumber
        db.accountName = accountName
        db.accountType = accountType
        db.date = dt.datetime.today()
        if accountType == "Bank Account":
            bankName = request.POST.get('bankName')
            bankbranch = request.POST.get('bankbranch')
            db.bankName = bankName
            db.bankBranchName = bankbranch        
        else:
            subscriber = request.POST.get('subscriber')
            db.subscriber = subscriber
        db.save()

        # create branch account
        account = Accounts()
        account.busRef = loginSessions(request, 'business')
        account.branchRef = loginSessions(request, 'branch')
        account.accountType = accountType
        account.accountName = accountName
        account.accountNumber = accountNumber
        account.save()
        activityLogs(request, loginSessions(request, 'user').userID, 'Online Acc Added', f'You added {accountType} with account number: {accountNumber}')
        return redirect('accounts', type='branch')


# delete online account
def deleteOnlineAccount(request, pk):
    with atomic():
        onlineAcc = OnlineAccounts.objects.get(Q(id=pk))
        acc = Accounts.objects.get(Q(accountNumber=onlineAcc.accountNumber)) 
        activityLogs(request, loginSessions(request, 'user').userID, 'Deleted Online Account', f'You deleted online account with account number {acc.accountNumber} with an amount of : {acc.accountBalance} as the time of deletion')
        acc.delete()
        onlineAcc.delete()
    return redirect('accounts', type='branch')
