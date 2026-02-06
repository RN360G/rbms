from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.db.models import Q, Sum
from businessApp.models import Business, BusinessBranch

# Create your views here.

class Richnet360(generic.View):
    def get(self, request):
        businesses = Business.objects.all()

        return render(request, 'richnet360/businesses.html', {'businesses': businesses})
    
    def post(self, request):
        return HttpResponse()

