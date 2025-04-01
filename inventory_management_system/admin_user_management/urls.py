from django.urls import path
from .views import manage_users, edit_user, delete_user, add_department_user

app_name = 'admin_user_management'
urlpatterns = [
    path('add-department-user/', add_department_user, name='add_department_user'),
    path('manage-users/', manage_users, name='manage_users'),
    path('edit-user/<int:user_id>/', edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', delete_user, name='delete_user'),
]