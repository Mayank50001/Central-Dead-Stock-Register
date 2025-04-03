from django.urls import path
from .views import cdsr_allocation_list , allocate_form , bulk_allocate_confirm , bulk_allocate, deallocate_form, bulk_deallocate, bulk_deallocate_confirm 

app_name = 'stock_management'

urlpatterns = [
    path("allocation/", cdsr_allocation_list, name="cdsr_allocation_list"),
    path("allocate/<int:cdsr_id>/", allocate_form, name="allocate_form"),
    path("allocation/bulk-confirm/", bulk_allocate_confirm, name="bulk_allocate_confirm"),
    path("allocation/bulk/", bulk_allocate, name="bulk_allocate"),
    path('deallocate/<int:cdsr_id>/', deallocate_form, name='deallocate_form'),
    path('bulk-deallocate/', bulk_deallocate, name='bulk_deallocate'),
    path('bulk-deallocate/confirm/', bulk_deallocate_confirm, name='bulk_deallocate_confirm'),
]