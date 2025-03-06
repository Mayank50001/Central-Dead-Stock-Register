from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser
from .forms import LoginForm, DepartmentUserCreationForm
from django.contrib.auth.decorators import login_required


@login_required
def add_department_user(request):
    if request.user.is_superuser:
        if request.method == "POST":
            form = DepartmentUserCreationForm(request.POST)
            if form.is_valid():
                department_user = form.save(commit=False)
                department_user.set_password(form.cleaned_data["password"])  # Hash the password
                department_user.save()
                return redirect("admin_dashboard")
        else:
            form = DepartmentUserCreationForm()
        return render(request, "accounts/add_department_user.html", {"form": form})
    else:
        return redirect("department_dashboard")



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
                if user.is_superuser:
                    return redirect("admin_dashboard")
                else:
                    return redirect("department_dashboard")
                    
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


# User Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


# Admin Dashboard View
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect("department_dashboard")  # If not admin, redirect to dept dashboard
    return render(request, "accounts/admin_dashboard.html")


# Department Dashboard View
@login_required
def department_dashboard(request):
    if request.user.is_superuser:
        return redirect("admin_dashboard")  # If admin, redirect to admin dashboard
    return render(request, "accounts/department_dashboard.html")
