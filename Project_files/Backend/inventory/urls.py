from django.urls import path

from . import views


urlpatterns = [

    # Inventory
    path(
        "",
        views.inventory,
        name="inventory"
    ),

    # Analytics
    path(
        "analytics/",
        views.analytics,
        name="analytics"
    ),

]