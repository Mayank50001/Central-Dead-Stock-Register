from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser
from .forms import LoginForm



# User Login View
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful!")
                
                # Redirect admin to their dashboard, else send to department dashboard
                if user.role == "admin":
                    return redirect("inventory:admin_dashboard")
                else:
                    return redirect("inventory:department_dashboard")
                    
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


# User Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")