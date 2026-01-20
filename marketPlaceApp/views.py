from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import generic


# Create your views here.


class GeneralMarket(generic.View):
    def get(self, request):
        return render(request, 'marketPlace/generalMarket.html')
    
    def post(self, request):
        return HttpResponse()
    


class AddBusiness(generic.View):
    def get(request):
        return render(request, 'businessApp/addBusiness.html')
    
    def post(request):
        return HttpResponse()
