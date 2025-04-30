from rest_framework import serializers
from django.contrib.auth.models import User as CustomUser

import bleach

from .models import Category, MenuItem, Cart, Order, OrderItem


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_active', 'last_login'] 


class CategorySerializer(serializers.ModelSerializer):
	
	class Meta:
		model = Category
		fields = ["id", "slug", "title"]


class MenuItemSerializer(serializers.ModelSerializer):
	category = CategorySerializer(read_only = True)
	category_id = serializers.IntegerField(write_only = True)
	class Meta:
		model = MenuItem
		fields = ["id", "title", "price", "featured", "category", "category_id"]

	def validate(self, attrs):
		attrs["title"] = bleach.clean(attrs["title"])
		if (attrs["price"] < 2):
			raise Serializers.ValidationError("Price should not be less than 2")
		if (attrs["category_id"] < 1):
			raise serializers.ValidationError("category id should not be negative or less than 1!!")
		return super().validate(attrs)


class CartItemSerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only = True)
	user_id = serializers.IntegerField(write_only = True)
	menuitem = MenuItemSerializer
	class Meta:
		model = Cart
		fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price', 'user_id']


class OrderSerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only = True)
	deliver_crew = UserSerializer(read_only = True)
	user_id = serializers.IntegerField(write_only = True)
	deliver_crew_id = serializers.IntegerField(write_only = True)

	class Meta:
		model = Order
		fields = ['id', 'user', 'deliver_crew', 'status', 'total', 'date', 'user_id', 'deliver_crew']


class OrderItemSerializer(serializers.ModelSerializer):
	order = UserSerializer(read_only = True)
	order_id = serializers.IntegerField(write_only = True)
	menuitem = MenuItemSerializer(read_only = True)
	menuitem_id = serializers.IntegerField(write_only = True)
	class Meta:
		model = OrderItem
		fields = ["id", "order", "menuitem", "quantity", "unit_price", "price", "order_id", "menuitem_id"]