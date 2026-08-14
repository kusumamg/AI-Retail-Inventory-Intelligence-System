from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from .ai_model import predict_demand


def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            # Check the user's role
            try:
                profile = user.userprofile

                if profile.role == "ADMIN":
                    return redirect("admin_dashboard")

                elif profile.role == "MANAGER":
                    return redirect("manager_dashboard")

            except Exception:
                pass

            # Fallback
            return redirect("dashboard")

        else:
            messages.error(
                request,
                "Invalid username or password."
            )

    return render(request, "login.html")


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


@login_required
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")


@login_required
def manager_dashboard(request):
    return render(request, "manager_dashboard.html")


@login_required
def inventory(request):

    prediction = None
    error = None

    if request.method == "POST":

        try:
            data = {
                "Store ID": request.POST.get("store_id"),
                "Product ID": request.POST.get("product_id"),
                "Category": request.POST.get("category"),
                "Region": request.POST.get("region"),

                "Inventory Level": float(
                    request.POST.get("inventory_level")
                ),

                "Price": float(
                    request.POST.get("price")
                ),

                "Discount": float(
                    request.POST.get("discount")
                ),

                "Weather Condition": request.POST.get(
                    "weather_condition"
                ),

                "Holiday/Promotion": int(
                    request.POST.get("holiday_promotion")
                ),

                "Competitor Pricing": float(
                    request.POST.get("competitor_pricing")
                ),

                "Seasonality": request.POST.get(
                    "seasonality"
                ),

                "Month": int(
                    request.POST.get("month")
                ),

                "Day": int(
                    request.POST.get("day")
                ),
            }

            prediction = predict_demand(data)

            prediction = round(
                float(prediction),
                2
            )

        except Exception as e:

            error = str(e)

    return render(
        request,
        "inventory.html",
        {
            "prediction": prediction,
            "error": error,
        }
    )