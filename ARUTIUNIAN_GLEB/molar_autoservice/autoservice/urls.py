"""
URL configuration for autoservice project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_page, name='home'),
    path('orders/', views.orders_page, name='orders'),
    path('edit/<int:order_id>/', views.edit_order, name='edit_order'),
    path('get-client-by-phone/', views.get_client_by_phone, name='get_client_by_phone'),
    path('schedule/', views.schedule_page, name='schedule'),
    path('schedule/delete/<int:shift_id>/', views.delete_shift, name='delete_shift'),
    path('schedule/publish/', views.publish_schedule, name='publish_schedule'),
    path('get-car-by-plate/', views.get_car_by_plate, name='get_car_by_plate'),
    path('check-plate-owner/', views.check_plate_owner, name='check_plate_owner'),
    path('repair/', views.repair_page, name='repair'),
    path('register/', views.register_view),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('register_staff/', views.register_staff_view),
]
