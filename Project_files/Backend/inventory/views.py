from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

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