from django.shortcuts import render, redirect
from django.views import generic
from django.http import Http404, HttpRequest, HttpResponseBadRequest, HttpResponse
from warehouseApp.models import Product
from businessApp.models import Business

# Create your views here.

def warehouse(request):

    if request.session['branchType'] == 'Retail & Wholesale Business':
        return redirect(to='salesProduct')
    
    elif request.session['branchType'] == 'Farming Business':
        return HttpResponse('Farming Business')
    
    elif request.session['branchType'] == 'Manufacturing Business':
        return HttpResponse('Manufacturing Business')

    elif request.session['branchType'] == 'Hotel Business':
        return HttpResponse('Hotel Business')

    elif request.session['branchType'] == 'Resturant & Bar Business':
        return HttpResponse('Resturant & Bar Business')

    elif request.session['branchType'] == 'Transportation Business':
        return HttpResponse('Transportation Business')

    elif request.session['branchType'] == 'Event Management':
        return HttpResponse('Event Management')

    elif request.session['branchType'] == 'Real Estate Business':
        return HttpResponse('Real Estate Business')







            



        
        