from django.urls import path
from businessApp import views

urlpatterns = [
    path('', views.AddBusiness.as_view(), name='addBusiness'),
    path('businesssettings', views.BusinessSettings.as_view(), name='businessSettings'),
    path('workinghours/<branchID>/<opt>', views.BusinessSettings.setWorkingHours, name='setWorkingHours'),
    path('onlinevisibility/<branchID>', views.BusinessSettings.onlineVisibility, name='onlineVisibility'),
    path('switchbranch', views.BusinessSettings.switchBranch, name='switchBranch'),
]