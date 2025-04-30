from django.contrib import admin

# Register your models here.
from .models import Category, MenuItem, Cart, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	pass


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
	pass


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
	pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	pass


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	pass