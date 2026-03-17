from django.urls import path
from accountsApp import views

urlpatterns = [
    path('<type>', views.AccountsView.as_view(), name='accounts'),
    path('expenses/', views.ExpensesView.as_view(), name='expenses'),
    path('deleteexpenses/<pk>', views.ExpensesView.deleteExpense, name='deleteExpenses'),
    path('cashanalysis/', views.CashAnalysisView.as_view(), name='cashAnalysis'),
    path('branchaccounttransactions/<pk>', views.AccountsView.branchAccountTransactions, name='branchAccountTransactions'),
    path('businessaccounttransactions/<pk>', views.AccountsView.businessAccountTransactions, name='businessAccountTransactions'),
    #path('transferfunds/', views.AccountsView.transferFunds, name='transferFunds'),
    path('authorizecashonhandtransfer/<transferType>/<pk>/<opt>/', views.SuspenseAccountView.authorizeFundTransfer, name='authorizeFundTransfer'),
    path('transferfundtosuspenseacc/<opt>/', views.SuspenseAccountView.transferToSuspenseAccount, name='transeferToSusoenseAccount'),
    path('deletefundtransferfrombranch/<pk>/', views.SuspenseAccountView.deleteFundTransferFromBranch, name='deleteFundTransferFromBranch'),
    path('deletefundtransferfrombusiness/<pk>/', views.SuspenseAccountView.deleteFundTransferFromBusiness, name='deleteFundTransferFromBusiness'),
    path('shortagepayments/<pk>/<payType>/', views.ShortagePayment.as_view(), name='shortagePayments'),
    path('withdrawalanddeposit/', views.AccountsView.depositAndWithdrawal, name='withdrawalPayments'),
    path('moveoverstobranchaccount/<pk>/', views.MoveOversToBranchAccount.as_view(), name='moveOversToBranchAccount'),
    path('depositandwithdrawalfrombranchacc/', views.AccountsView.depositAndWithdrawalFromBranchAcc, name='depositAndWithdrawalFromBranchAcc'),
    path('payroll/', views.PayRoll.as_view(), name='payRoll'),
    path('salesincomestatement/', views.IncomeStatementView.as_view(), name='salesIncomeState'),
    path('addedonlineaccount/', views.addOnlinePaymentAccounts, name='addOnlinePaymentAccounts'), 
    path('deleteonlineaccount/<pk>', views.deleteOnlineAccount, name='deleteOnlineAccount'),
]