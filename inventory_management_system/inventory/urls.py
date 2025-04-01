from django.urls import path
from .views import admin_dashboard, department_dashboard, add_item, inventory_list , cdsr_allocation_list , allocate_form , bulk_allocate_confirm , bulk_allocate, deallocate_form, bulk_deallocate, bulk_deallocate_confirm , department_inventory_list, edit_item, delete_item, manage_stock_by_register, register_inventory_list, add_register_item, add_register, delete_register , delete_register_item, edit_register_item
app_name = 'inventory'

urlpatterns = [
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('department-dashboard/', department_dashboard, name='department_dashboard'),
    path('add-item/', add_item, name='add_item'),  # ✅ New URL
    path('inventory-list/', inventory_list, name='inventory_list'),  # ✅ New URL
    path("allocation/", cdsr_allocation_list, name="cdsr_allocation_list"),
    path("allocate/<int:cdsr_id>/", allocate_form, name="allocate_form"),
    path("allocation/bulk-confirm/", bulk_allocate_confirm, name="bulk_allocate_confirm"),
    path("allocation/bulk/", bulk_allocate, name="bulk_allocate"),
    path('deallocate/<int:cdsr_id>/', deallocate_form, name='deallocate_form'),
    path('bulk-deallocate/', bulk_deallocate, name='bulk_deallocate'),
    path('bulk-deallocate/confirm/', bulk_deallocate_confirm, name='bulk_deallocate_confirm'),
    path('department/inventory/', department_inventory_list, name='department_inventory_list'),
    path('edit-item/<int:cdsr_id>/', edit_item, name='edit_item'),
    path('delete-item/<int:cdsr_id>/', delete_item, name='delete_item'),
    
    path('manage-stock-by-register/', manage_stock_by_register, name='manage_stock_by_register'),
    path('register/<path:register_name>/inventory/', register_inventory_list, name='register_inventory_list'),
    path('register/<path:register_name>/add-item/', add_register_item, name='add_register_item'),
    path('register/add/', add_register, name='add_register'),
    path('register/<path:register_name>/delete/', delete_register, name='delete_register'),
    path('register/<path:register_name>/delete-item/<int:cdsr_id>/', delete_register_item, name='delete_register_item'),
    path('register/<path:register_name>/edit-item/<int:cdsr_id>/', edit_register_item, name='edit_register_item'),
]
