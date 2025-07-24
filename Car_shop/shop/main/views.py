from django.http import Http404
from django.shortcuts import render, get_object_or_404

from main.models import Car, Sale

def cars_list_view(request):
    cars = Car.objects.all().order_by('model')
    template_name = 'main/list.html'
    context = {'cars': cars}
    return render(request, template_name, context)

def car_details_view(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    template_name = 'main/details.html'
    context = {'car': car}
    return render(request, template_name, context)

def sales_by_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    sales = Sale.objects.filter(car=car).order_by('-created_at')
    template_name = 'main/sales.html'
    context = {
        'car': car,
        'sales': sales
    }
    return render(request, template_name, context)
