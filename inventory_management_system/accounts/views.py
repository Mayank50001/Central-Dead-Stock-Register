from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import CustomUser
from .forms import LoginForm

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def redirect_with_no_cache(url_name, *args, **kwargs):
    """
    Utility function to redirect with cache control headers to prevent browser back button
    """
    response = HttpResponseRedirect(reverse(url_name, args=args, kwargs=kwargs))
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Frame-Options'] = 'DENY'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Clear-Site-Data'] = '"cache", "cookies", "storage"'
    return response

# User Login View
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                # Get current device info
                current_ip = get_client_ip(request)
                print(current_ip)
                print(user.last_ip_address)
                print(user.last_login_device)
                
                # Check if user is already logged in from another device
                if user.last_ip_address and user.last_ip_address != current_ip:
                    messages.error(request, "This account is already logged in from another device.")
                    return redirect("accounts:login")
                
                # Update user's device information
                user.last_ip_address = current_ip
                user.last_login_device = timezone.now()
                user.last_logout_device = None
                user.save()
                
                # Login the user
                login(request, user)
                messages.success(request, "Login successful!")
                
                # Redirect based on role
                if user.role == "admin":
                    return redirect("inventory:admin_dashboard")
                else:
                    return redirect("inventory:department_dashboard")
                    
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    
    return render(request, "accounts/login.html", {"form": form})

def logout_view(request):
    if request.user.is_authenticated:
        # Clear device information on logout
        user = request.user
        user.last_ip_address = None
        user.last_login_device = None
        user.last_logout_device = timezone.now()
        user.save()
    
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect_with_no_cache("accounts:login")