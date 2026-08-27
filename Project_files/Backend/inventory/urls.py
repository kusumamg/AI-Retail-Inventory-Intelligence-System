from django.urls import path

from . import views


urlpatterns = [

    # Inventory
    path(
        "",
        views.inventory,
        name="inventory"
    ),

    # AI Forecast
    path(
        "forecast/",
        views.ai_forecast,
        name="ai_forecast"
    ),

    # Analytics
    path(
        "analytics/",
        views.analytics,
        name="analytics"
    ),

    # Reports
    path(
        "reports/",
        views.reports,
        name="reports"
    ),

    # Export Report
    path(
        "reports/export/",
        views.export_report_csv,
        name="export_report_csv"
    ),

    # Products
    path(
        "products/",
        views.products,
        name="products"
    ),

    # Add Product
    path(
        "products/add/",
        views.add_product,
        name="add_product"
    ),

    # Edit Product
    path(
        "products/edit/<int:product_id>/",
        views.edit_product,
        name="edit_product"
    ),

    
    path(
    "users/",
    views.users,
    name="users"
    ),
    
    path(
    "stores/",
    views.stores,
    name="stores"
),

]