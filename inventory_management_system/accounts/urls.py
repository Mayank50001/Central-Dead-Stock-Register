from django.urls import path
from .views import login_view, logout_view, admin_dashboard, department_dashboard, add_department_user

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),  # Admin Dashboard
    path("department-dashboard/", department_dashboard, name="department_dashboard"),  # Dept Dashboard
    path("add-department-user/", add_department_user, name="add_department_user"),  # Add User Function
]
