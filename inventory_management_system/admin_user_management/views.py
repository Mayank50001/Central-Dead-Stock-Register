from django.shortcuts import render , redirect
from .forms import DepartmentUserCreationForm , DEPARTMENT_CHOICES
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse 
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from inventory.decorators import role_required

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


# Create your views here.
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@role_required(allowed_roles=['admin'])
def add_department_user(request):
    if request.method == "POST":
        form = DepartmentUserCreationForm(request.POST)
        if form.is_valid():
            department_user = form.save(commit=False)
            department_user.set_password(form.cleaned_data["password"])
            department_user.role = "department"
            department_user.department = form.cleaned_data["department"]
            department_user.save()
            messages.success(request, "Department user added successfully!")
            return redirect_with_no_cache("inventory:admin_dashboard")
    else:
        form = DepartmentUserCreationForm()
    return render(request, "admin_user_management/add_department_user.html", {"form": form})


@user_passes_test(is_admin)
def manage_users(request):
    users = get_user_model().objects.filter(role='department')
    return render(request, "admin_user_management/manage_users.html", {'users': users})

@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(get_user_model(), id=user_id, role='department')

    if request.method == 'POST':
        department = request.POST.get('department')
        password = request.POST.get('password')
        is_active = request.POST.get('is_active') == 'on'
        
        print(department)
        print(is_active)

        user.department = department
        user.is_active = is_active
        
        if password != '':
            user.set_password(password)
        
        print(user.password)
        user.save()
        messages.success(request, 'User updated successfully.')
        return redirect('admin_user_management:manage_users')
    
    return render(request, 'admin_user_management/edit_user.html', {
        'user': user,
        'departments': DEPARTMENT_CHOICES  # Using the imported DEPARTMENT_CHOICES
    })

@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(get_user_model(), id=user_id, role='department')
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('admin_user_management:manage_users')
    
    return render(request, 'admin_user_management/delete_user.html', {'user': user})