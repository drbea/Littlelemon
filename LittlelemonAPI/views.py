from django.shortcuts import render
# from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.models import User, Group

from rest_framework import viewsets, status , generics
from rest_framework.response import Response
from rest_framework.decorators import api_view #, renderer_classes, throttle_classes
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, BasePermission, IsAdminUser, AllowAny

from . models import MenuItem, Category, Cart, Order, OrderItem
from . serializers import MenuItemSerializer, UserSerializer, OrderSerializer, CartItemSerializer
from . throttles import TenCallsPerMinute

# Create your views here.

MANAGER_GROUP_NAME = "managers"  
DELIVER_GROUP_NAME = "deliver_crew"  
CUSTOMER_GROUP_NAME = "customer"  
class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='customer').exists()

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='manager').exists()

class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='delivery_crew').exists()


class UserList(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer


class MenuItemView(viewsets.ModelViewSet):

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    ordering_fields = ["price", "inventory"]
    search_fields = ["title", "category__name"]
    throttling_classes = [AnonRateThrottle, TenCallsPerMinute]

    def get_permissions(self):
    	""" Determines which permissions must be applied for each action."""
    	if self.action == 'list':
    		return [AllowAny()]
    	elif self.action in ['create', 'update', 'partial_update', 'destroy']:
    		return [IsAuthenticated(), IsManager()]
    	return [IsAuthenticated()] # Par défaut, les autres actions nécessitent une authentification


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsManager])
def manager_users_list(request):
    """
    List all users of 'Managers' group (GET)
    or add an exist user to 'Managers' group (POST).
    """
    try:
        manager_group = Group.objects.get(name=MANAGER_GROUP_NAME)
    except Group.DoesNotExist:
        return Response({"error": f"The '{MANAGER_GROUP_NAME}' does'nt exist."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        managers = manager_group.user_set.all()
        serializer = UserSerializer(managers, many=True)  
        return Response(serializer.data)
    elif request.method == "POST":
        username = request.data.get('username') 
        if not username:
            return Response({"error": "The 'username' field is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": f"The user: '{username}' does'nt exist."}, status=status.HTTP_404_NOT_FOUND)

        user.groups.add(manager_group)
        return Response({"message": f"The user '{username}' has been add to '{MANAGER_GROUP_NAME}' group."}, status=status.HTTP_201_CREATED)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsManager])
def remove_from_managers(self, userId):
    """
    Remove User from Managers group'.
    """
    try:
        manager_group = Group.objects.get(name=MANAGER_GROUP_NAME)
    except Group.DoesNotExist:
        return Response({"error": f"The '{MANAGER_GROUP_NAME}' group does'nt exist."}, status=status.HTTP_404_NOT_FOUND)

    try:
        user = User.objects.get(id=userId)
    except User.DoesNotExist:
        return Response({"error": f"There is not user with an 'ID : {userId}"}, status=status.HTTP_404_NOT_FOUND)

    if manager_group in user.groups.all():
        user.groups.remove(manager_group)
        return Response({"message": f"The user '{user.username}' has been remove from'{MANAGER_GROUP_NAME}' group."}, status=status.HTTP_200_OK)
    else:
        return Response({"message": f"User '{user.username}' was not in '{MANAGER_GROUP_NAME}' group."}, status=status.HTTP_200_OK)



@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsManager])
def deliver_users_list(request):
    """
    List all users of 'Managers' group (GET)
    or add an exist user to 'Managers' group (POST).
    """
    try:
        deliver_group = Group.objects.get(name=DELIVER_GROUP_NAME)
    except Group.DoesNotExist:
        return Response({"error": f"The '{DELIVER_GROUP_NAME}' does'nt exist."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        deliver = deliver_group.user_set.all()
        serializer = UserSerializer(deliver, many=True)  
        return Response(serializer.data)
    elif request.method == "POST":
        username = request.data.get('username') 
        if not username:
            return Response({"error": "The 'username' field is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": f"The user: '{username}' does'nt exist."}, status=status.HTTP_404_NOT_FOUND)

        user.groups.add(deliver_group)
        return Response({"message": f"The user '{username}' has been add to '{DELIVER_GROUP_NAME}' group."}, status=status.HTTP_201_CREATED)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class OrderView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]  

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='delivery_crew').exists():
            return Order.objects.filter(delivery_crew=user)
        elif user.groups.filter(name='customer').exists():
            return Order.objects.filter(user=user)
        return Order.objects.none()  # Default to no orders if no group match

    def perform_create(self, serializer):
        if self.request.user.groups.filter(name='customer').exists():
            cart_items = Cart.objects.filter(user=self.request.user)
            if not cart_items.exists():
                raise serializers.ValidationError("Le panier est vide.")

            order = serializer.save(user=self.request.user)
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    quantity=cart_item.quantity,
                    price=cart_item.menu_item.price * cart_item.quantity  # Example price calculation
                )
            cart_items.delete()
        else:
            raise permissions.PermissionDenied("Seuls les clients peuvent créer une commande.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if user.groups.filter(name='customer').exists() and instance.user != user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user = request.user

        if user.groups.filter(name='manager').exists():
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif user.groups.filter(name='delivery_crew').exists():
            # Delivery crew can only update the status
            if 'status' in request.data and request.data['status'] in [0, 1]:
                serializer = self.get_serializer(instance, data={'status': request.data['status']}, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            else:
                return Response({"error": "Seul le statut (0 ou 1) peut être mis à jour par l'équipe de livraison."}, status=status.HTTP_400_BAD_REQUEST)
        elif user.groups.filter(name='customer').exists():
            return Response({"error": "Les clients ne peuvent pas modifier les commandes existantes."}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs, partial=True)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        if user.groups.filter(name='manager').exists():
            return super().destroy(request, *args, **kwargs)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)



class CartItemList(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            menu_item_id = self.request.data.get('menu_item')
            quantity = self.request.data.get('quantity', 1)  # Default quantity is 1
            menu_item = MenuItem.objects.get(pk=menu_item_id)
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Le menu item spécifié n'existe pas.")
        except KeyError:
            raise serializers.ValidationError("Le champ 'menu_item' est requis.")

        # Check if the item is already in the cart
        existing_cart_item = Cart.objects.filter(user=self.request.user, menu_item=menu_item).first()

        if existing_cart_item:
            existing_cart_item.quantity += quantity
            existing_cart_item.save()
            serializer = self.get_serializer(existing_cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer.save(user=self.request.user, menu_item=menu_item, quantity=quantity)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """
        Supprime tous les éléments du panier de l'utilisateur courant.
        """
        cart_items = Cart.objects.filter(user=request.user)
        if cart_items.exists():
            cart_items.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "Votre panier est déjà vide."}, status=status.HTTP_200_OK)

