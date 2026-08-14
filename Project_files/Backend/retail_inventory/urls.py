"""
URL configuration for retail_inventory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
"""
URL configuration for retail_inventory project.
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView

from inventory import views


urlpatterns = [

    # Django Admin
    path("admin/", admin.site.urls),

    # Login
    path(
        "login/",
        views.login_view,
        name="login"
    ),

    # Dashboard
    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    # Admin Dashboard
    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    # Manager Dashboard
    path(
        "manager-dashboard/",
        views.manager_dashboard,
        name="manager_dashboard"
    ),

    # Inventory
    path(
        "inventory/",
        include("inventory.urls")
    ),

    # Logout
    path(
        "logout/",
        LogoutView.as_view(
            next_page="/login/"
        ),
        name="logout"
    ),
]