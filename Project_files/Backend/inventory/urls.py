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

    # Reports
    path(
        "reports/",
        views.reports,
        name="reports"
    ),

        path(
        "reports/export/",
        views.export_report_csv,
        name="export_report_csv"
    ),

]

