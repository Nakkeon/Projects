from django.contrib import admin
from .models import Client, Car, Sale

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_name', 'phone_number')
    search_fields = ('name', 'last_name', 'phone_number')

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('model', 'year', 'price', 'color')
    list_filter = ('body_type', 'fuel_type', 'drive_unit')
    search_fields = ('model',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('car', 'client', 'created_at')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'