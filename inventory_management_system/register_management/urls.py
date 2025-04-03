from django.urls import path
from .views import (
    manage_stock_by_register,
    register_inventory_list,
    add_register_item,
    add_register,
    delete_register,
    delete_register_item,
    edit_register_item
)
app_name = 'register_management'

urlpatterns = [
    path('manage-stock-by-register/', manage_stock_by_register, name='manage_stock_by_register'),
    path('<path:register_name>/inventory/', register_inventory_list, name='register_inventory_list'),
    path('<path:register_name>/add-item/', add_register_item, name='add_register_item'),
    path('add/', add_register, name='add_register'),
    path('<path:register_name>/delete/', delete_register, name='delete_register'),
    path('<path:register_name>/delete-item/<int:cdsr_id>/', delete_register_item, name='delete_register_item'),
    path('<path:register_name>/edit-item/<int:cdsr_id>/', edit_register_item, name='edit_register_item'),

]