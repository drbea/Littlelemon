from django.urls import path, include

from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'menu-items', views.MenuItemView, basename='menu-item')
router.register(r'user-list', views.UserList, basename='user-list')


urlpatterns = [
    path("groups/manager/users", views.manager_users_list, name = "manager_users_list"),  #[POST, GET]
    path("groups/manager/users/<int:userId>", views.remove_from_managers, name = "remove-managers"), # [POST]
    
    path("groups/delivers/users", views.deliver_users_list, name = "deliver_users_list"),  #[POST, GET]
    path("groups/delivers/users/<int:userId>", views.deliver_users_list, name = "deliver_users_list"),  #[POST, GET]
    
    path('orders', views.OrderView.as_view(), name='order-list-create'),
    path('orders/<int:pk>', views.OrderView.as_view(), name='order-detail'),

    path('cart/menu-items', views.CartItemList.as_view(), name='cart-items-list-create'),

    path("", include(router.urls)),
]
