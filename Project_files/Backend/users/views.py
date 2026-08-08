from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render


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

            # Check user's role
            try:
                role = user.profile.role
            except Exception:
                role = None

            if role == "ADMIN":
                return redirect("admin_dashboard")

            elif role == "MANAGER":
                return redirect("manager_dashboard")

            else:
                messages.error(
                    request,
                    "Your account does not have a valid role."
                )
                logout(request)

        else:
            messages.error(
                request,
                "Invalid username or password."
            )

    return render(request, "login.html")


def logout_view(request):

    logout(request)

    return redirect("login")