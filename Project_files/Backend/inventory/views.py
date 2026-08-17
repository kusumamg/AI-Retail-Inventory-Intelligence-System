from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from .models import Product
from users.models import Store

from .ai_model import predict_demand


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