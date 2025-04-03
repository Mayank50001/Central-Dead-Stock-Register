from django.urls import path
from .views import admin_dashboard, department_dashboard, add_item, inventory_list, department_inventory_list, edit_item, delete_item
app_name = 'inventory'

urlpatterns = [
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('department-dashboard/', department_dashboard, name='department_dashboard'),
    path('add-item/', add_item, name='add_item'),  # ✅ New URL
    path('inventory-list/', inventory_list, name='inventory_list'),  # ✅ New URL
    path('department/inventory/', department_inventory_list, name='department_inventory_list'),
    path('edit-item/<int:cdsr_id>/', edit_item, name='edit_item'),
    path('delete-item/<int:cdsr_id>/', delete_item, name='delete_item'),
     
]
