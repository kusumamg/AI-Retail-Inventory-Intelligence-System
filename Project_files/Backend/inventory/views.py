from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.db import models

from .models import Product
from users.models import Store

from .ai_model import predict_demand
from django.utils import timezone

import math
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    # --------------------------------------------------------
    # Already logged in
    # --------------------------------------------------------

    if request.user.is_authenticated:

        try:

            profile = request.user.profile

            if profile.role == "ADMIN":
                return redirect("admin_dashboard")

            elif profile.role == "MANAGER":
                return redirect("manager_dashboard")

        except Exception:

            messages.error(
                request,
                "User profile not found."
            )

            return redirect("login")

    # --------------------------------------------------------
    # Login form submitted
    # --------------------------------------------------------

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        # ----------------------------------------------------
        # Valid username and password
        # ----------------------------------------------------

        if user is not None:

            login(request, user)

            try:

                profile = user.profile

                # ADMIN
                if profile.role == "ADMIN":

                    return redirect(
                        "admin_dashboard"
                    )

                # STORE MANAGER
                elif profile.role == "MANAGER":

                    return redirect(
                        "manager_dashboard"
                    )

                # Unknown role
                else:

                    messages.error(
                        request,
                        "Your account does not have a valid role."
                    )

                    return redirect("login")

            except Exception:

                messages.error(
                    request,
                    "User profile not found."
                )

                return redirect("login")

        # ----------------------------------------------------
        # Invalid username/password
        # ----------------------------------------------------

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

    return render(
        request,
        "login.html"
    )


# ============================================================
# COMMON DASHBOARD
# ============================================================

@login_required
def dashboard(request):

    try:

        profile = request.user.profile

        if profile.role == "ADMIN":

            return redirect(
                "admin_dashboard"
            )

        elif profile.role == "MANAGER":

            return redirect(
                "manager_dashboard"
            )

    except Exception:

        messages.error(
            request,
            "User profile not found."
        )

        return redirect("login")

    return redirect("login")


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@login_required
def admin_dashboard(request):

    # Get all products from all stores
    products = Product.objects.all()

    # Get all stores
    stores = Store.objects.all()

    # Overall statistics
    total_products = products.count()

    total_stock = sum(
        product.inventory_level
        for product in products
    )

    low_stock = products.filter(
        inventory_level__gt=0,
        inventory_level__lt=25
    ).count()

    out_of_stock = products.filter(
        inventory_level=0
    ).count()

    # Number of active stores
    active_stores = stores.filter(
        is_active=True
    ).count()

    # Latest product prediction
    latest_product = products.order_by(
        "-updated_at"
    ).first()

    latest_prediction = None

    if latest_product:
        latest_prediction = latest_product.predicted_demand

    return render(
        request,
        "admin_dashboard.html",
        {
            "products": products,
            "stores": stores,

            "total_products": total_products,
            "total_stock": total_stock,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,

            "active_stores": active_stores,

            "latest_product": latest_product,
            "latest_prediction": latest_prediction,
        }
    )

# ============================================================
# STORE MANAGER DASHBOARD
# ============================================================

@login_required
def manager_dashboard(request):

    # Get the logged-in user's profile
    profile = request.user.profile

    # Get the store assigned to this manager
    store = profile.store

    # If no store is assigned
    if store is None:
        return render(
            request,
            "manager_dashboard.html",
            {
                "store": None,
                "error": "No store has been assigned to your account."
            }
        )

    # Get products belonging to this manager's store
    products = Product.objects.filter(
        store=store
    )

    # Dashboard statistics
    total_products = products.count()

    total_stock = sum(
        product.inventory_level
        for product in products
    )

    low_stock = products.filter(
        inventory_level__gt=0,
        inventory_level__lt=25
    ).count()

    out_of_stock = products.filter(
        inventory_level=0
    ).count()

    # Get latest product with prediction
    latest_product = products.order_by(
        "-updated_at"
    ).first()

    latest_prediction = None

    if latest_product:
        latest_prediction = latest_product.predicted_demand

    return render(
        request,
        "manager_dashboard.html",
        {
            "store": store,
            "products": products,
            "total_products": total_products,
            "total_stock": total_stock,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "latest_product": latest_product,
            "latest_prediction": latest_prediction,
        }
    )


# ============================================================
# ANALYTICS
# ============================================================

@login_required
def analytics(request):

    # =====================================================
    # GET ALL PRODUCTS
    # =====================================================

    products = Product.objects.select_related("store").all()

    # =====================================================
    # OVERALL SUMMARY
    # =====================================================

    total_products = products.count()

    total_stock = sum(
        product.inventory_level
        for product in products
    )

    low_stock = products.filter(
        inventory_level__gt=0,
        inventory_level__lt=25
    ).count()

    out_of_stock = products.filter(
        inventory_level=0
    ).count()

    # =====================================================
    # CATEGORY ORDER
    # =====================================================

    category_order = [
        "Electronics",
        "Clothing",
        "Groceries",
        "Toys",
        "Furniture",
    ]

    category_data = []

    # =====================================================
    # BUILD CATEGORY-WISE DATA
    # =====================================================

    for category_name in category_order:

        category_products = products.filter(
            category=category_name
        )

        # Do not display categories with no products
        if not category_products.exists():
            continue

        # -------------------------------------------------
        # CATEGORY TOTALS
        # -------------------------------------------------

        category_stock = sum(
            product.inventory_level
            for product in category_products
        )

        category_demand = sum(
            product.predicted_demand or 0
            for product in category_products
        )

        category_product_count = category_products.count()

        # -------------------------------------------------
        # CATEGORY COVERAGE
        # -------------------------------------------------

        if category_demand > 0:
            category_coverage = (
                category_stock / category_demand
            ) * 100
        else:
            category_coverage = 0

        # -------------------------------------------------
        # CATEGORY PRODUCTS
        # -------------------------------------------------

        category_items = []

        for product in category_products:

            # Determine stock status
            if product.inventory_level == 0:

                status = "OUT_OF_STOCK"

            elif product.inventory_level < 25:

                status = "LOW_STOCK"

            else:

                status = "IN_STOCK"

            category_items.append({

                "subcategory": (
                    product.subcategory
                    if product.subcategory
                    else product.category
                ),

                "region": product.region,

                "inventory": product.inventory_level,

                "predicted_demand": (
                    product.predicted_demand or 0
                ),

                "status": status,

            })

        # -------------------------------------------------
        # STORE CATEGORY DATA
        # -------------------------------------------------

        category_data.append({

            "name": category_name,

            "product_count": category_product_count,

            "stock": category_stock,

            "demand": category_demand,

            "coverage": category_coverage,

            "items": category_items,

        })

    # =====================================================
    # BAR CHART SCALE
    # =====================================================

    if category_data:

        maximum_value = max(
            max(
                category["stock"],
                category["demand"]
            )
            for category in category_data
        )

        if maximum_value <= 0:
            maximum_value = 1

        for category in category_data:

            category["chart_stock_height"] = (
                category["stock"] / maximum_value
            ) * 100

            category["chart_demand_height"] = (
                category["demand"] / maximum_value
            ) * 100

    # =====================================================
    # RENDER ANALYTICS PAGE
    # =====================================================

    return render(
        request,
        "analytics.html",
        {
            "products": products,

            "total_products": total_products,

            "total_stock": total_stock,

            "low_stock": low_stock,

            "out_of_stock": out_of_stock,

            "category_data": category_data,
        }
    )

# ============================================================
# INVENTORY / AI DEMAND PREDICTION
# ============================================================

@login_required
def inventory(request):

    prediction = None
    error = None
    product = None

    # --------------------------------------------------------
    # Get active stores
    # --------------------------------------------------------

    stores = Store.objects.filter(
        is_active=True
    )

    # ========================================================
    # FORM SUBMISSION
    # ========================================================

    if request.method == "POST":

        try:

            # ------------------------------------------------
            # Get form values
            # ------------------------------------------------

            store_id = request.POST.get(
                "store_id"
            )

            product_id = request.POST.get(
                "product_id"
            )

            category = request.POST.get(
                "category"
            )

            subcategory = request.POST.get(
                "subcategory"
          )

            region = request.POST.get(
                "region"
            )

            inventory_level = float(
                request.POST.get(
                    "inventory_level"
                )
            )

            price = float(
                request.POST.get(
                    "price"
                )
            )

            discount = float(
                request.POST.get(
                    "discount"
                )
            )

            weather_condition = request.POST.get(
                "weather_condition"
            )

            holiday_promotion = int(
                request.POST.get(
                    "holiday_promotion"
                )
            )

            competitor_pricing = float(
                request.POST.get(
                    "competitor_pricing"
                )
            )

            seasonality = request.POST.get(
                "seasonality"
            )

            month = int(
                request.POST.get(
                    "month"
                )
            )

            day = int(
                request.POST.get(
                    "day"
                )
            )

            # ------------------------------------------------
            # Basic validation
            # ------------------------------------------------

            if not store_id:
                raise ValueError(
                    "Please select a store."
                )

            if not product_id:
                raise ValueError(
                    "Please enter a Product ID."
                )

            if not category:
                raise ValueError(
                    "Please select a category."
                )

            if not region:
                raise ValueError(
                    "Please select a region."
                )

            if not weather_condition:
                raise ValueError(
                    "Please select a weather condition."
                )

            if not seasonality:
                raise ValueError(
                    "Please select a season."
                )

            if month < 1 or month > 12:
                raise ValueError(
                    "Month must be between 1 and 12."
                )

            if day < 1 or day > 31:
                raise ValueError(
                    "Day must be between 1 and 31."
                )

            # ------------------------------------------------
            # Find selected store
            # ------------------------------------------------

            store = Store.objects.get(
                store_code=store_id,
                is_active=True
            )

            # =================================================
            # PREPARE DATA FOR AI MODEL
            # =================================================

            data = {

                "Store ID": store_id,

                "Product ID": product_id,

                "Category": category,

                "subcategory": subcategory,

                "Region": region,

                "Inventory Level": inventory_level,

                "Price": price,

                "Discount": discount,

                "Weather Condition": weather_condition,

                "Holiday/Promotion": holiday_promotion,

                "Competitor Pricing": competitor_pricing,

                "Seasonality": seasonality,

                "Month": month,

                "Day": day,
            }

            # =================================================
            # AI DEMAND PREDICTION
            # =================================================

            prediction = predict_demand(
                data
            )

            prediction = round(
                prediction,
                2
            )

            # =================================================
            # SAVE / UPDATE PRODUCT
            # =================================================

            product, created = Product.objects.update_or_create(

                store=store,

                product_id=product_id,

                defaults={

                    "category": category,

                    "subcategory": subcategory,

                    "region": region,

                    "inventory_level": int(
                        inventory_level
                    ),

                    "price": price,

                    "discount": discount,

                    "weather_condition":
                        weather_condition,

                    "holiday_promotion":
                        bool(holiday_promotion),

                    "competitor_pricing":
                        competitor_pricing,

                    "seasonality":
                        seasonality,

                    "predicted_demand":
                        prediction,
                }
            )

        # =====================================================
        # ERROR HANDLING
        # =====================================================

        except Store.DoesNotExist:

            error = (
                "The selected store does not exist "
                "or is inactive."
            )

        except (ValueError, TypeError):

            error = (
                "Please enter valid values for all "
                "required fields."
            )

        except Exception as e:

            error = str(e)

    # ========================================================
    # RENDER INVENTORY PAGE
    # ========================================================

    return render(

        request,

        "inventory.html",

        {
            "prediction": prediction,

            "error": error,

            "product": product,

            "stores": stores,
        }
    )



@login_required
def reports(request):

    # ============================================================
    # GET PRODUCTS
    # ============================================================

    products = Product.objects.select_related("store").all()

    # ============================================================
    # FILTERS
    # ============================================================

    selected_category = request.GET.get("category", "")
    selected_store = request.GET.get("store", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    if selected_category:
        products = products.filter(
            category=selected_category
        )

    if selected_store:
        products = products.filter(
            store_id=selected_store
        )

    if from_date:
        products = products.filter(
            created_at__date__gte=from_date
        )

    if to_date:
        products = products.filter(
            created_at__date__lte=to_date
        )

    # ============================================================
    # OVERALL REPORT SUMMARY
    # ============================================================

    total_products = products.count()

    total_stock = sum(
        product.inventory_level
        for product in products
    )

    low_stock = products.filter(
        inventory_level__gt=0,
        inventory_level__lt=25
    ).count()

    out_of_stock = products.filter(
        inventory_level=0
    ).count()

    # ============================================================
    # CATEGORY REPORTS
    # ============================================================

    category_order = [
        "Electronics",
        "Clothing",
        "Groceries",
        "Toys",
        "Furniture",
    ]

    category_reports = []

    for category_name in category_order:

        category_products = products.filter(
            category=category_name
        )

        if not category_products.exists():
            continue

        # ------------------------------
        # Category totals
        # ------------------------------

        category_stock = sum(
            product.inventory_level
            for product in category_products
        )

        category_demand = sum(
            product.predicted_demand or 0
            for product in category_products
        )

        category_low_stock = category_products.filter(
            inventory_level__gt=0,
            inventory_level__lt=25
        ).count()

        category_out_of_stock = category_products.filter(
            inventory_level=0
        ).count()

        category_attention = (
            category_low_stock +
            category_out_of_stock
        )

        # ------------------------------
        # Category coverage
        # ------------------------------

        if category_demand > 0:

            category_coverage = (
                category_stock /
                category_demand
            ) * 100

        else:

            category_coverage = 0

        # ------------------------------
        # Product rows
        # ------------------------------

        product_rows = []

        for product in category_products:

            if product.inventory_level == 0:

                status = "OUT_OF_STOCK"

            elif product.inventory_level < 25:

                status = "LOW_STOCK"

            else:

                status = "IN_STOCK"

            if product.predicted_demand and product.predicted_demand > 0:

                demand_coverage = (
                    product.inventory_level /
                    product.predicted_demand
                ) * 100

            else:

                demand_coverage = 0

            product_rows.append({

                "product_id":
                    product.product_id,

                "subcategory":
                    product.subcategory,

                "store":
                    product.store.name,

                "store_code":
                    product.store.store_code,

                "region":
                    product.region,

                "inventory":
                    product.inventory_level,

                "predicted_demand":
                    product.predicted_demand or 0,

                "demand_coverage":
                    round(
                        demand_coverage,
                        1
                    ),

                "status":
                    status,
            })

        # ------------------------------
        # Add category report
        # ------------------------------

        category_reports.append({

            "category":
                category_name,

            "products":
                product_rows,

            "total_products":
                len(product_rows),

            "total_stock":
                category_stock,

            "total_demand":
                round(
                    category_demand,
                    2
                ),

            "coverage":
                round(
                    category_coverage,
                    1
                ),

            "low_stock":
                category_low_stock,

            "out_of_stock":
                category_out_of_stock,

            "attention":
                category_attention,
        })

    # ============================================================
    # AVAILABLE FILTER OPTIONS
    # ============================================================

    available_categories = (
        Product.objects
        .values_list(
            "category",
            flat=True
        )
        .distinct()
        .order_by("category")
    )

    available_stores = (
        Store.objects
        .all()
        .order_by("name")
    )

    # ============================================================
    # CONTEXT
    # ============================================================

    context = {

        # Overall summary
        "total_products":
            total_products,

        "total_stock":
            total_stock,

        "low_stock":
            low_stock,

        "out_of_stock":
            out_of_stock,

        # Category reports
        "category_reports":
            category_reports,

        # Filters
        "available_categories":
            available_categories,

        "available_stores":
            available_stores,

        "selected_category":
            selected_category,

        "selected_store":
            selected_store,

        "from_date":
            from_date,

        "to_date":
            to_date,
    }

    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        "reports.html",
        context
    )

def export_report_csv(request):
    products = Product.objects.all()

    selected_category = request.GET.get("category", "")
    selected_store = request.GET.get("store", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    if selected_category:
        products = products.filter(category=selected_category)

    if selected_store:
        products = products.filter(store_id=selected_store)

    if from_date:
        products = products.filter(created_at__date__gte=from_date)

    if to_date:
        products = products.filter(created_at__date__lte=to_date)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="inventory_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Product ID",
        "Category",
        "Subcategory",
        "Store",
        "Store Code",
        "Region",
        "Current Stock",
        "Predicted Demand",
        "Stock Coverage (%)",
        "Price",
        "Discount (%)",
        "Stock Status"
    ])

    for product in products:

        if product.inventory_level == 0:
            status = "OUT_OF_STOCK"
        elif product.inventory_level < 25:
            status = "LOW_STOCK"
        else:
            status = "IN_STOCK"

        if product.predicted_demand > 0:
            coverage = (
                product.inventory_level /
                product.predicted_demand
            ) * 100
        else:
            coverage = 0

        writer.writerow([
            product.product_id,
            product.category,
            product.subcategory,
            product.store.name,
            product.store.store_code,
            product.region,
            product.inventory_level,
            round(product.predicted_demand, 2),
            round(coverage, 1),
            product.price,
            product.discount,
            status
        ])

    return response
def export_report_pdf(request):
    products = Product.objects.all()

    selected_category = request.GET.get("category", "")
    selected_store = request.GET.get("store", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    if selected_category:
        products = products.filter(category=selected_category)

    if selected_store:
        products = products.filter(store_id=selected_store)

    if from_date:
        products = products.filter(created_at__date__gte=from_date)

    if to_date:
        products = products.filter(created_at__date__lte=to_date)

    category_order = [
        "Electronics",
        "Clothing",
        "Groceries",
        "Toys",
        "Furniture",
    ]

    category_data = []

    for category in category_order:
        category_products = products.filter(category=category)

        if not category_products.exists():
            continue

        total_stock = sum(
            p.inventory_level for p in category_products
        )

        total_demand = sum(
            p.predicted_demand for p in category_products
        )

        low_stock = category_products.filter(
            inventory_level__gt=0,
            inventory_level__lt=25
        ).count()

        out_of_stock = category_products.filter(
            inventory_level=0
        ).count()

        category_data.append({
            "category": category,
            "products": category_products,
            "stock": total_stock,
            "demand": total_demand,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
        })

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    story = []

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------

    story.append(
        Paragraph(
            "AI-Based Retail Inventory Intelligence Report",
            title_style
        )
    )

    story.append(Spacer(1, 6))

    report_date = timezone.now().strftime("%d-%m-%Y %H:%M")

    story.append(
        Paragraph(
            f"Report Generated: {report_date}",
            normal_style
        )
    )

    story.append(Spacer(1, 12))

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    total_products = products.count()

    total_stock = sum(
        p.inventory_level for p in products
    )

    total_demand = sum(
        p.predicted_demand for p in products
    )

    total_low_stock = products.filter(
        inventory_level__gt=0,
        inventory_level__lt=25
    ).count()

    total_out_of_stock = products.filter(
        inventory_level=0
    ).count()

    summary_data = [
        ["Total Products", "Current Stock", "Predicted Demand",
         "Low Stock", "Out of Stock"],

        [
            str(total_products),
            str(total_stock),
            f"{total_demand:.2f}",
            str(total_low_stock),
            str(total_out_of_stock),
        ]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            45 * mm,
            45 * mm,
            50 * mm,
            40 * mm,
            40 * mm,
        ]
    )

    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, 1), colors.whitesmoke),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(summary_table)
    story.append(Spacer(1, 15))

    # --------------------------------------------------
    # CATEGORY CHART
    # --------------------------------------------------

    story.append(
        Paragraph("Category-wise Stock vs Predicted Demand", heading_style)
    )

    chart_data = [
        ["Category", "Current Stock", "Predicted Demand"]
    ]

    for item in category_data:
        chart_data.append([
            item["category"],
            str(item["stock"]),
            f"{item['demand']:.2f}"
        ])

    chart_table = Table(
        chart_data,
        colWidths=[60 * mm, 55 * mm, 60 * mm]
    )

    chart_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D4AF37")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(chart_table)
    story.append(Spacer(1, 18))

    # --------------------------------------------------
    # CATEGORY REPORTS
    # --------------------------------------------------

    for item in category_data:

        category = item["category"]

        story.append(
            Paragraph(
                f"{category} Inventory Report",
                heading_style
            )
        )

        story.append(Spacer(1, 6))

        category_summary = [
            [
                "Current Stock",
                "Predicted Demand",
                "Low Stock",
                "Out of Stock"
            ],
            [
                str(item["stock"]),
                f"{item['demand']:.2f}",
                str(item["low_stock"]),
                str(item["out_of_stock"])
            ]
        ]

        summary = Table(
            category_summary,
            colWidths=[
                50 * mm,
                55 * mm,
                45 * mm,
                45 * mm
            ]
        )

        summary.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )

        story.append(summary)
        story.append(Spacer(1, 8))

        # Product table

        table_data = [
            [
                "Product ID",
                "Subcategory",
                "Store",
                "Region",
                "Current Stock",
                "Predicted Demand",
                "Status"
            ]
        ]

        status_values = []

        for product in item["products"]:

            if product.inventory_level == 0:
                status = "OUT OF STOCK"
            elif product.inventory_level < 25:
                status = "LOW STOCK"
            else:
                status = "IN STOCK"

            status_values.append(status)

            table_data.append([
                product.product_id,
                product.subcategory,
                product.store.name,
                product.region,
                str(product.inventory_level),
                f"{product.predicted_demand:.2f}",
                status
            ])

        product_table = Table(
            table_data,
            repeatRows=1,
            colWidths=[
                30 * mm,
                40 * mm,
                45 * mm,
                35 * mm,
                30 * mm,
                40 * mm,
                35 * mm
            ]
        )

        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]

        for row_number, status in enumerate(status_values, start=1):

            if status == "OUT OF STOCK":
                table_style.append(
                    (
                        "BACKGROUND",
                        (6, row_number),
                        (6, row_number),
                        colors.HexColor("#F8D7DA")
                    )
                )

            elif status == "LOW STOCK":
                table_style.append(
                    (
                        "BACKGROUND",
                        (6, row_number),
                        (6, row_number),
                        colors.HexColor("#FFF3CD")
                    )
                )

            else:
                table_style.append(
                    (
                        "BACKGROUND",
                        (6, row_number),
                        (6, row_number),
                        colors.HexColor("#D4EDDA")
                    )
                )

        product_table.setStyle(TableStyle(table_style))

        story.append(product_table)
        story.append(Spacer(1, 18))

    # --------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------

    document.build(story)

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="retail_inventory_report.pdf"'
    )

    return response
# ============================================================
# PRODUCTS
# ============================================================

@login_required
def products(request):

    search = request.GET.get("search", "").strip()

    products = Product.objects.select_related(
        "store"
    ).all()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        products = products.filter(
            models.Q(product_id__icontains=search)
            | models.Q(store__name__icontains=search)
            | models.Q(store__store_code__icontains=search)
            | models.Q(category__icontains=search)
            | models.Q(subcategory__icontains=search)
        )

    # --------------------------------------------------------
    # CATEGORY ORDER
    # --------------------------------------------------------

    category_order = [
        "Electronics",
        "Clothing",
        "Groceries",
        "Toys",
        "Furniture",
    ]

    products = products.order_by(
        "category",
        "subcategory",
        "product_id"
    )

    # --------------------------------------------------------
    # CATEGORY SECTIONS
    # --------------------------------------------------------

    category_sections = []

    for category in category_order:

        category_products = products.filter(
            category=category
        )

        if category_products.exists():

            category_sections.append({
                "name": category,
                "products": category_products,
            })

    # --------------------------------------------------------
    # EXTRA CATEGORIES
    # --------------------------------------------------------

    existing_categories = set(category_order)

    other_categories = (
        products
        .values_list("category", flat=True)
        .distinct()
    )

    for category in other_categories:

        if category not in existing_categories:

            category_products = products.filter(
                category=category
            )

            if category_products.exists():

                category_sections.append({
                    "name": category,
                    "products": category_products,
                })

    return render(
        request,
        "products.html",
        {
            "products": products,
            "category_sections": category_sections,
            "search": search,
        }
    )

@login_required
def add_product(request):

    stores = Store.objects.filter(
        is_active=True
    )

    error = None

    # Values supported by the trained AI model
    product_ids = [
        f"P{i:04d}"
        for i in range(1, 21)
    ]

    categories = [
        "Clothing",
        "Electronics",
        "Furniture",
        "Groceries",
        "Toys",
    ]

    regions = [
        "East",
        "North",
        "South",
        "West",
    ]

    weather_conditions = [
        "Cloudy",
        "Rainy",
        "Snowy",
        "Sunny",
    ]

    seasons = [
        "Autumn",
        "Spring",
        "Summer",
        "Winter",
    ]

    if request.method == "POST":

        try:

            # ====================================================
            # GET FORM DATA
            # ====================================================

            product_id = request.POST.get(
                "product_id"
            ).strip()

            store_id = request.POST.get(
                "store_id"
            )

            category = request.POST.get(
                "category"
            ).strip()

            subcategory = request.POST.get(
                "subcategory"
            ).strip()

            region = request.POST.get(
                "region"
            ).strip()

            inventory_level = int(
                request.POST.get(
                    "inventory_level"
                )
            )

            price = float(
                request.POST.get(
                    "price"
                )
            )

            discount = float(
                request.POST.get(
                    "discount"
                )
            )

            weather_condition = request.POST.get(
                "weather_condition"
            ).strip()

            holiday_promotion = (
                request.POST.get(
                    "holiday_promotion"
                ) == "1"
            )

            competitor_pricing = float(
                request.POST.get(
                    "competitor_pricing"
                )
            )

            seasonality = request.POST.get(
                "seasonality"
            ).strip()


            # ====================================================
            # VALIDATE MODEL-SUPPORTED VALUES
            # ====================================================

            if product_id not in product_ids:

                raise ValueError(
                    "Please select a valid Product ID "
                    "between P0001 and P0020."
                )

            if category not in categories:

                raise ValueError(
                    "Please select a valid category."
                )

            if region not in regions:

                raise ValueError(
                    "Please select a valid region."
                )

            if weather_condition not in weather_conditions:

                raise ValueError(
                    "Please select a valid weather condition."
                )

            if seasonality not in seasons:

                raise ValueError(
                    "Please select a valid season."
                )


            # ====================================================
            # GET STORE
            # ====================================================

            store = Store.objects.get(
                store_code=store_id
            )


            # ====================================================
            # CHECK DUPLICATE PRODUCT
            # ====================================================

            if Product.objects.filter(
                store=store,
                product_id=product_id
            ).exists():

                error = (
                    f"Product {product_id} already exists "
                    f"in {store.name}."
                )

            else:

                # =================================================
                # AI MODEL INPUT
                # =================================================

                current_date = timezone.now()

                input_data = {

                    "Store ID":
                        store.store_code,

                    "Product ID":
                        product_id,

                    "Category":
                        category,

                    "Region":
                        region,

                    "Inventory Level":
                        inventory_level,

                    "Price":
                        price,

                    "Discount":
                        discount,

                    "Weather Condition":
                        weather_condition,

                    "Holiday/Promotion":
                        int(holiday_promotion),

                    "Competitor Pricing":
                        competitor_pricing,

                    "Seasonality":
                        seasonality,

                    "Month":
                        current_date.month,

                    "Day":
                        current_date.day,
                }


                # =================================================
                # AI DEMAND PREDICTION
                # =================================================

                prediction = predict_demand(
                    input_data
                )

                # Prevent negative predictions
                prediction = max(
                    0,
                    prediction
                )

                prediction = round(
                    prediction,
                    2
                )


                # =================================================
                # CREATE PRODUCT WITH AI PREDICTION
                # =================================================

                Product.objects.create(

                    product_id=product_id,

                    store=store,

                    category=category,

                    subcategory=subcategory,

                    region=region,

                    inventory_level=inventory_level,

                    price=price,

                    discount=discount,

                    weather_condition=weather_condition,

                    holiday_promotion=holiday_promotion,

                    competitor_pricing=competitor_pricing,

                    seasonality=seasonality,

                    predicted_demand=prediction,
                )


                return redirect(
                    "products"
                )


        except Store.DoesNotExist:

            error = (
                "Please select a valid store."
            )


        except (ValueError, TypeError):

            error = (
                "Please enter valid values "
                "for the product details."
            )


        except Exception as e:

            error = str(e)


    return render(
        request,
        "add_product.html",
        {
            "stores": stores,
            "error": error,
        }
    )


@login_required
def edit_product(request, product_id):

    product = Product.objects.get(
        id=product_id
    )

    stores = Store.objects.filter(
        is_active=True
    )

    error = None

    if request.method == "POST":

        try:

            store_id = request.POST.get("store_id")

            product.product_id = request.POST.get(
                "product_id"
            ).strip()

            product.category = request.POST.get(
                "category"
            ).strip()

            product.subcategory = request.POST.get(
                "subcategory"
            ).strip()

            product.region = request.POST.get(
                "region"
            ).strip()

            product.inventory_level = int(
                request.POST.get("inventory_level")
            )

            product.price = float(
                request.POST.get("price")
            )

            product.discount = float(
                request.POST.get("discount")
            )

            product.weather_condition = request.POST.get(
                "weather_condition"
            ).strip()

            product.holiday_promotion = (
                request.POST.get("holiday_promotion") == "1"
            )

            product.competitor_pricing = float(
                request.POST.get("competitor_pricing")
            )

            product.seasonality = request.POST.get(
                "seasonality"
            ).strip()

            product.store = Store.objects.get(
                store_code=store_id
            )

            # Check duplicate Product ID in same store
            duplicate = Product.objects.filter(
                store=product.store,
                product_id=product.product_id
            ).exclude(
                id=product.id
            ).exists()

            if duplicate:

                error = (
                    f"Product {product.product_id} "
                    f"already exists in this store."
                )

            else:

                product.save()

                return redirect("products")

        except Store.DoesNotExist:

            error = "Please select a valid store."

        except (ValueError, TypeError):

            error = (
                "Please enter valid numeric values."
            )

        except Exception as e:

            error = str(e)

    return render(
        request,
        "edit_product.html",
        {
            "product": product,
            "stores": stores,
            "error": error,
        }
    )

@login_required
def delete_product(request, product_id):

    if request.method == "POST":

        product = Product.objects.get(
            id=product_id
        )

        product.delete()

        return redirect("products")

    return redirect("products")

# ============================================================
# AI FORECAST
# ============================================================

@login_required
def ai_forecast(request):

    products = Product.objects.select_related(
        "store"
    ).all()


    # =====================================================
    # GENERATE AI PREDICTIONS
    # =====================================================

    if request.method == "POST":

        from django.contrib import messages
        from django.utils import timezone
        from .ai_model import predict_demand

        successful_predictions = 0
        failed_predictions = 0

        current_date = timezone.now()


        for product in products:

            try:

                # Build input using the same
                # features used during training

                input_data = {

                    "Store ID":
                        product.store.store_code,

                    "Product ID":
                        product.product_id,

                    "Category":
                        product.category,

                    "Region":
                        product.region,

                    "Inventory Level":
                        product.inventory_level,

                    "Price":
                        product.price,

                    "Discount":
                        product.discount,

                    "Weather Condition":
                        product.weather_condition,

                    "Holiday/Promotion":
                        int(
                            product.holiday_promotion
                        ),

                    "Competitor Pricing":
                        product.competitor_pricing,

                    "Seasonality":
                        product.seasonality,

                    "Month":
                        current_date.month,

                    "Day":
                        current_date.day,
                }


                # Generate prediction

                prediction = predict_demand(
                    input_data
                )


                # Prevent negative demand

                prediction = max(
                    0,
                    prediction
                )


                # Save prediction

                product.predicted_demand = round(
                    prediction,
                    2
                )

                product.save(
                    update_fields=[
                        "predicted_demand",
                        "updated_at"
                    ]
                )


                successful_predictions += 1


            except Exception as e:

                print(
                    f"Prediction failed for "
                    f"{product.product_id}: {e}"
                )

                failed_predictions += 1


        # =================================================
        # RESULT MESSAGE
        # =================================================

        if successful_predictions > 0:

            messages.success(
                request,
                f"AI predictions generated successfully "
                f"for {successful_predictions} product(s)."
            )


        if failed_predictions > 0:

            messages.warning(
                request,
                f"{failed_predictions} product(s) "
                f"could not be predicted. "
                f"Check the terminal for details."
            )


        return redirect(
            "ai_forecast"
        )


    # =====================================================
    # DISPLAY FORECAST
    # =====================================================

    predicted_products = products.filter(
        predicted_demand__isnull=False
    )


    # =====================================================
    # TOTAL PREDICTED DEMAND
    # =====================================================

    total_predicted_demand = sum(
        product.predicted_demand or 0
        for product in predicted_products
    )


    # =====================================================
    # AVERAGE PREDICTED DEMAND
    # =====================================================

    average_predicted_demand = (

        total_predicted_demand /
        predicted_products.count()

        if predicted_products.exists()

        else 0
    )


    # =====================================================
    # DEMAND COVERAGE
    # =====================================================

    for product in predicted_products:

        if product.predicted_demand > 0:

            product.demand_coverage = round(

                (
                    product.inventory_level /
                    product.predicted_demand
                ) * 100,

                1
            )

        else:

            product.demand_coverage = 0


    # =====================================================
    # CATEGORY-WISE FORECAST DATA
    # =====================================================

    category_order = [

        "Electronics",

        "Clothing",

        "Groceries",

        "Toys",

        "Furniture",
    ]


    category_forecasts = []


    for category in category_order:

        category_products = [
    product
    for product in predicted_products
    if product.category == category
]


        if not category_products:

            continue


        # -------------------------------------------------
        # Category predicted demand
        # -------------------------------------------------

        category_demand = sum(

            product.predicted_demand or 0

            for product in category_products
        )


        # -------------------------------------------------
        # Category current stock
        # -------------------------------------------------

        category_stock = sum(

            product.inventory_level

            for product in category_products
        )


        # -------------------------------------------------
        # Category demand coverage
        # -------------------------------------------------

        if category_demand > 0:

            category_coverage = (

                category_stock /
                category_demand

            ) * 100

        else:

            category_coverage = 0


        # -------------------------------------------------
        # Replenishment count
        # -------------------------------------------------

        replenishment_count = sum(

            1

            for product in category_products

            if (
                product.predicted_demand or 0
            ) > product.inventory_level
        )


        # -------------------------------------------------
        # Store category information
        # -------------------------------------------------

        category_forecasts.append({

            "name":
                category,

            "products":
                category_products,

            "product_count":
                len(category_products),

            "predicted_demand":
                round(
                    category_demand,
                    2
                ),

            "current_stock":
                category_stock,

            "coverage":
                round(
                    category_coverage,
                    1
                ),

            "replenishment_count":
                replenishment_count,
        })


    # =====================================================
    # RENDER AI FORECAST PAGE
    # =====================================================

    return render(

        request,

        "ai_forecast.html",

        {

            "products":
                products,

            "predicted_products":
                predicted_products,

            "total_predicted_demand":
                round(
                    total_predicted_demand,
                    2
                ),

            "average_predicted_demand":
                round(
                    average_predicted_demand,
                    2
                ),

            "category_forecasts":
                category_forecasts,
        }
    )

# ============================================================
# SMART ALERTS
# ============================================================
@login_required
def alerts(request):

    products = Product.objects.select_related("store").all()

    # ============================================================
    # FILTERS
    # ============================================================

    alert_filter = request.GET.get("type", "ALL")
    selected_category = request.GET.get("category", "")

    if selected_category:
        products = products.filter(
            category=selected_category
        )

    alert_data = []

    # ============================================================
    # BUILD ALERT DATA
    # ============================================================

    for product in products:

        predicted_demand = product.predicted_demand or 0
        current_stock = product.inventory_level

        # --------------------------------------------------------
        # ALERT TYPE
        # --------------------------------------------------------

        if current_stock == 0:

            alert_type = "OUT_OF_STOCK"
            alert_title = "Out of Stock"
            alert_message = (
                "This product currently has no available stock."
            )
            alert_priority = "High"

        elif predicted_demand > current_stock:

            alert_type = "REPLENISHMENT"
            alert_title = "Replenishment Needed"
            alert_message = (
                "Predicted demand is greater than "
                "the current inventory level."
            )
            alert_priority = "High"

        elif current_stock < 25:

            alert_type = "LOW_STOCK"
            alert_title = "Low Stock"
            alert_message = (
                "Inventory level is below the "
                "defined low-stock threshold."
            )
            alert_priority = "Medium"

        else:

            continue

        # --------------------------------------------------------
        # DEMAND COVERAGE
        # --------------------------------------------------------

        if predicted_demand > 0:

            demand_coverage = round(
                (current_stock / predicted_demand) * 100,
                1
            )

        else:

            demand_coverage = 0

        # --------------------------------------------------------
        # REORDER CALCULATION
        # --------------------------------------------------------

        safety_stock = predicted_demand * 0.10

        required_stock = predicted_demand + safety_stock

        recommended_reorder = max(
            0,
            math.ceil(
                required_stock - current_stock
            )
        )

        # --------------------------------------------------------
        # STORE ALERT
        # --------------------------------------------------------

        alert_data.append({

            "product_id":
                product.product_id,

            "store":
                product.store.name,

            "store_code":
                product.store.store_code,

            "category":
                product.category,

            "subcategory":
                product.subcategory,

            "region":
                product.region,

            "inventory":
                current_stock,

            "predicted_demand":
                predicted_demand,

            "demand_coverage":
                demand_coverage,

            "recommended_reorder":
                recommended_reorder,

            "safety_stock":
                round(safety_stock, 2),

            "required_stock":
                round(required_stock, 2),

            "alert_type":
                alert_type,

            "alert_title":
                alert_title,

            "alert_message":
                alert_message,

            "priority":
                alert_priority,
        })

    # ============================================================
    # ALERT SUMMARY
    # ============================================================

    total_alerts = len(alert_data)

    out_of_stock_alerts = sum(
        1
        for alert in alert_data
        if alert["alert_type"] == "OUT_OF_STOCK"
    )

    replenishment_alerts = sum(
        1
        for alert in alert_data
        if alert["alert_type"] == "REPLENISHMENT"
    )

    low_stock_alerts = sum(
        1
        for alert in alert_data
        if alert["alert_type"] == "LOW_STOCK"
    )

    # ============================================================
    # ALERT TYPE FILTER
    # ============================================================

    filtered_alert_data = alert_data

    if alert_filter != "ALL":

        filtered_alert_data = [
            alert
            for alert in alert_data
            if alert["alert_type"] == alert_filter
        ]

    # ============================================================
    # CATEGORY-WISE ALERT DATA
    # ============================================================

    category_order = [
        "Electronics",
        "Clothing",
        "Groceries",
        "Toys",
        "Furniture",
    ]

    category_alerts = []

    for category in category_order:

        category_alert_data = [
            alert
            for alert in filtered_alert_data
            if alert["category"] == category
        ]

        if category_alert_data:

            category_alerts.append({

                "category":
                    category,

                "alerts":
                    category_alert_data,
            })

    # ============================================================
    # AVAILABLE CATEGORIES
    # ============================================================

    available_categories = (
        Product.objects
        .values_list(
            "category",
            flat=True
        )
        .distinct()
        .order_by("category")
    )

    # ============================================================
    # RENDER
    # ============================================================

    return render(
        request,
        "alerts.html",
        {

            "alert_data":
                filtered_alert_data,

            "category_alerts":
                category_alerts,

            "available_categories":
                available_categories,

            "selected_category":
                selected_category,

            "total_alerts":
                total_alerts,

            "out_of_stock_alerts":
                out_of_stock_alerts,

            "replenishment_alerts":
                replenishment_alerts,

            "low_stock_alerts":
                low_stock_alerts,

            "alert_filter":
                alert_filter,
        }
    )
# ============================================================
# USERS
# ============================================================

@login_required
def users(request):

    # Only administrators can access Users
    try:
        profile = request.user.profile

        if profile.role != "ADMIN":
            return redirect("dashboard")

    except Exception:
        return redirect("login")

    # Get all registered users
    from django.contrib.auth.models import User

    all_users = User.objects.all().order_by(
        "username"
    )

    return render(
        request,
        "users.html",
        {
            "users": all_users,
        }
    )

# ============================================================
# STORES
# ============================================================

@login_required
def stores(request):

    # Only administrators can access Stores
    try:
        profile = request.user.profile

        if profile.role != "ADMIN":
            return redirect("dashboard")

    except Exception:
        return redirect("login")

    # Get all stores
    all_stores = Store.objects.all().order_by(
        "store_code"
    )

    return render(
        request,
        "stores.html",
        {
            "stores": all_stores,
        }
    )

# =========================================================
# SYSTEM MANAGEMENT
# =========================================================

# =========================================================
# SYSTEM MANAGEMENT
# =========================================================

@login_required
def system_management(request):

    return render(
        request,
        "system_management.html"
    )

# ============================================================
# SETTINGS
# ============================================================

@login_required
def settings(request):

    user = request.user

    if request.method == "POST":

        action = request.POST.get("action")

        # ====================================================
        # UPDATE PROFILE
        # ====================================================

        if action == "profile":

            username = request.POST.get(
                "username"
            ).strip()

            email = request.POST.get(
                "email"
            ).strip()

            if not username:

                messages.error(
                    request,
                    "Username cannot be empty."
                )

            elif not email:

                messages.error(
                    request,
                    "Email cannot be empty."
                )

            else:

                # Check if username is already used
                from django.contrib.auth.models import User

                username_exists = User.objects.filter(
                    username=username
                ).exclude(
                    id=user.id
                ).exists()

                if username_exists:

                    messages.error(
                        request,
                        "This username is already in use."
                    )

                else:

                    user.username = username
                    user.email = email
                    user.save()

                    messages.success(
                        request,
                        "Profile settings updated successfully."
                    )

                    return redirect("settings")


        # ====================================================
        # CHANGE PASSWORD
        # ====================================================

        elif action == "password":

            current_password = request.POST.get(
                "current_password"
            )

            new_password = request.POST.get(
                "new_password"
            )

            confirm_password = request.POST.get(
                "confirm_password"
            )

            if not user.check_password(
                current_password
            ):

                messages.error(
                    request,
                    "Current password is incorrect."
                )

            elif len(new_password) < 8:

                messages.error(
                    request,
                    "New password must contain at least 8 characters."
                )

            elif new_password != confirm_password:

                messages.error(
                    request,
                    "New passwords do not match."
                )

            else:

                user.set_password(
                    new_password
                )

                user.save()

                # Keep user logged in after password change
                from django.contrib.auth import update_session_auth_hash

                update_session_auth_hash(
                    request,
                    user
                )

                messages.success(
                    request,
                    "Password changed successfully."
                )

                return redirect("settings")


        # ====================================================
        # APPLICATION PREFERENCES
        # ====================================================

        elif action == "preferences":

            theme = request.POST.get(
                "theme",
                "light"
            )

            notifications = request.POST.get(
                "notifications"
            ) == "on"

            low_stock_threshold = request.POST.get(
                "low_stock_threshold",
                "25"
            )

            try:

                low_stock_threshold = int(
                    low_stock_threshold
                )

                if low_stock_threshold < 1:

                    raise ValueError

            except (ValueError, TypeError):

                low_stock_threshold = 25

                messages.error(
                    request,
                    "Low-stock threshold must be a positive number."
                )

            else:

                request.session["theme"] = theme

                request.session["notifications"] = notifications

                request.session[
                    "low_stock_threshold"
                ] = low_stock_threshold

                request.session.modified = True

                messages.success(
                    request,
                    "Application preferences saved successfully."
                )

                return redirect("settings")


    # ========================================================
    # CURRENT SETTINGS
    # ========================================================

    current_theme = request.session.get(
        "theme",
        "light"
    )

    notifications_enabled = request.session.get(
        "notifications",
        True
    )

    low_stock_threshold = request.session.get(
        "low_stock_threshold",
        25
    )


    # ========================================================
    # DISPLAY SETTINGS PAGE
    # ========================================================

    return render(
        request,
        "settings.html",
        {
            "current_theme": current_theme,
            "notifications_enabled":
                notifications_enabled,
            "low_stock_threshold":
                low_stock_threshold,
        }
    )