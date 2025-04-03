from django.shortcuts import render , get_object_or_404 , redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from inventory.decorators import role_required
from inventory.models import CDSR, DDSR
from urllib.parse import unquote
from django.http import HttpResponse , HttpResponseRedirect
from django.urls import reverse
from django.utils.text import slugify
from datetime import datetime
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import timedelta

import csv
from django.contrib import messages
from inventory.forms import ItemForm

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
@login_required
@role_required(allowed_roles=['admin'])
def manage_stock_by_register(request):
    # Get distinct register names with their counts and total values
    registers = CDSR.objects.values('cdsr_name').annotate(
        item_count=Count('cdsr_id'),
        total_value=Sum('total_cost')
    ).order_by('cdsr_name')
    
    # Format the data for the template
    register_list = []
    for register in registers:
        if register['cdsr_name']:  # Only include non-empty register names
            register_list.append({
                'name': register['cdsr_name'],
                'item_count': register['item_count'],
                'total_value': "{:,.2f}".format(register['total_value'] or 0)
            })
    
    return render(request, 'register_management/manage_stock_by_register.html', {
        'registers': register_list
    })

@login_required
@role_required(allowed_roles=['admin'])
def register_inventory_list(request, register_name):
    # Decode the URL-encoded register name
    register_name = unquote(register_name)
    
    # Get all items for this register, excluding the dummy item if it exists
    items_list = CDSR.objects.filter(cdsr_name=register_name).exclude(
        product_description="Register Created",
        product_category="System",
        product_type="System",
        product_quantity=0,
        single_cost=0,
        total_cost=0,
        remaining_quantity=0
    )
    fields = [field.name for field in CDSR._meta.fields]

    # Date Range Filter
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if from_date:
        items_list = items_list.filter(date_of_purchase__gte=from_date)
    if to_date:
        items_list = items_list.filter(date_of_purchase__lte=to_date)

    # Sorting Logic
    sort_by = request.GET.get("sort_by", "cdsr_id")
    order = request.GET.get("order", "asc")
    if order == "desc":
        sort_by = f"-{sort_by}"
    items_list = items_list.order_by(sort_by)

    # Filtering Logic
    filter_queries = Q()
    filter_fields = request.GET.getlist("filter_field")
    filter_values = request.GET.getlist("filter_value")

    for field, value in zip(filter_fields, filter_values):
        if field and value:
            filter_queries &= Q(**{f"{field}__icontains": value})

    items_list = items_list.filter(filter_queries)

    # Export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="{slugify(register_name)}_inventory_{timestamp}.csv"'
        
        writer = csv.writer(response)
        # Write headers
        writer.writerow([field.replace('_', ' ').title() for field in fields])
        
        # Write data
        for item in items_list:
            writer.writerow([getattr(item, field) for field in fields])
        
        return response

    # Pagination
    paginator = Paginator(items_list, 50)
    page_number = request.GET.get("page")
    items = paginator.get_page(page_number)

    context = {
        "items": items,
        "fields": fields,
        "register_name": register_name,
        "sort_by": request.GET.get("sort_by", ""),
        "order": request.GET.get("order", "asc"),
        "filter_fields": filter_fields,
        "filter_values": filter_values,
        "from_date": from_date,
        "to_date": to_date
    }

    return render(request, "register_management/register_inventory_list.html", context)

@login_required
@role_required(allowed_roles=['admin'])
def add_register_item(request, register_name):
    # Decode the URL-encoded register name
    register_name = unquote(register_name)
    
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.cdsr_name = register_name  # Set the register name
            
            # Check if this is the first item being added to a new register
            dummy_id = request.session.get('new_register_dummy_id')
            if dummy_id:
                try:
                    # Get the dummy item
                    CDSR.objects.get(cdsr_id=dummy_id, cdsr_name=register_name).delete()
                    # Update the dummy item with the new item's data
                    item.cdsr_id = dummy_id  # Keep the same ID
                    item.save()
                    # Clear the session
                    del request.session['new_register_dummy_id']
                    messages.success(request, "Item added successfully!")
                    return redirect_with_no_cache("register_management:register_inventory_list", register_name=register_name)
                except CDSR.DoesNotExist:
                    # If dummy item not found, just save as new item
                    item.save()
                    messages.success(request, "Item added successfully!")
                    return redirect_with_no_cache("register_management:register_inventory_list", register_name=register_name)
            else:
                # Normal save for subsequent items
                item.save()
                messages.success(request, "Item added successfully!")
                return redirect_with_no_cache("register_management:register_inventory_list", register_name=register_name)
    else:
        form = ItemForm()
        # Set the initial value and make the field disabled
        form.fields['cdsr_name'].initial = register_name
        
        # # Add the register name to the form's choices if it's not already there
        # if (register_name, register_name) not in form.fields['cdsr_name'].choices:
        #     form.fields['cdsr_name'].choices.append((register_name, register_name))
    
    context = {
        "form": form,
        "register_name": register_name
    }
    return render(request, "register_management/add_register_item.html", context)

@login_required
@role_required(allowed_roles=['admin'])
def delete_register_item(request, register_name ,  cdsr_id):
    cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
    register_name = cdsr_item.cdsr_name
    if request.method == "POST":
        allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
        if allocations.exists():
            messages.error(request, "Cannot delete item with existing allocations. Please deallocate first.")
            return redirect_with_no_cache("register_management:register_inventory_list", register_name=cdsr_item.cdsr_name)
            
        if CDSR.objects.filter(cdsr_name=register_name).count() == 1:
            cdsr_item.delete()
            messages.success(request, "Last item deleted from the register. Register deleted successfully!.....Add the register back on demand")
            return redirect_with_no_cache("register_management:manage_stock_by_register")
            
        messages.success(request, "Item deleted successfully!")
        return redirect_with_no_cache("register_management:register_inventory_list", register_name=cdsr_item.cdsr_name)
    
    allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
    total_allocated = allocations.aggregate(total=Sum('accepted_product_quantity'))['total'] or 0
    
    context = {
        "cdsr_item": cdsr_item,
        "allocations": allocations,
        "total_allocated": total_allocated
    }
    
    return render(request, "register_management/delete_register_item.html", context)

@login_required
@role_required(allowed_roles=['admin'])
def edit_register_item(request , register_name , cdsr_id):
    cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
    
    if request.method == "POST":
        form = ItemForm(request.POST, instance=cdsr_item)
        if form.is_valid():
            old_quantity = cdsr_item.product_quantity
            new_quantity = form.cleaned_data['product_quantity']
            
            total_allocated = DDSR.objects.filter(cdsr_table_id=cdsr_id).aggregate(
                total=Sum('accepted_product_quantity')
            )['total'] or 0
            
            if new_quantity < total_allocated:
                messages.error(request, f"Cannot reduce quantity below allocated amount ({total_allocated})")
                return render(request, "register_management/edit_register_item.html", {
                    "form": form,
                    "cdsr_item": cdsr_item
                })
            
            updated_item = form.save(commit=False)
            quantity_diff = new_quantity - old_quantity
            updated_item.remaining_quantity += quantity_diff
            
            if 'single_cost' in form.changed_data:
                updated_item.total_cost = updated_item.product_quantity * updated_item.single_cost
            
            updated_item.save()
            
            if 'single_cost' in form.changed_data:
                DDSR.objects.filter(cdsr_table_id=cdsr_id).update(
                    cost_unit=updated_item.single_cost,
                    total_cost=models.F('accepted_product_quantity') * updated_item.single_cost
                )
            
            messages.success(request, "Item updated successfully!")
            return redirect_with_no_cache("register_management:register_inventory_list", register_name=register_name)
    else:
        form = ItemForm(instance=cdsr_item)
    
    allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
    total_allocated = allocations.aggregate(total=Sum('accepted_product_quantity'))['total'] or 0
    
    context = {
        "form": form,
        "cdsr_item": cdsr_item,
        "allocations": allocations,
        "total_allocated": total_allocated
    }
    
    return render(request, "register_management/edit_register_item.html", context)

@login_required
@role_required(allowed_roles=['admin'])
def add_register(request):
    if request.method == "POST":
        register_name = request.POST.get('register_name')
        if register_name:
            # Check if register already exists
            if CDSR.objects.filter(cdsr_name=register_name).exists():
                messages.error(request, f"Register '{register_name}' already exists.")
                return redirect('register_management:manage_stock_by_register')
            
            # Create a new register by adding a dummy item
            dummy_item = CDSR.objects.create(
                cdsr_name=register_name,
                cdsr_no="0",
                cdsr_pg_no="0",
                product_description="Register Created",
                product_category="System",
                product_type="System",
                product_quantity=0,
                single_cost=0,
                total_cost=0,
                remaining_quantity=0,
                date_of_purchase=now(),
                purchase_year=str(now().year)
            )
            
            # Store the dummy item's ID in the session
            request.session['new_register_dummy_id'] = dummy_item.cdsr_id
            messages.success(request, f"Register '{register_name}' created successfully.")
        else:
            messages.error(request, "Register name is required.")
    return redirect('register_management:manage_stock_by_register')

@login_required
@role_required(allowed_roles=['admin'])
def delete_register(request, register_name):
    if request.method == "POST":
        # Get all items for this register, excluding the dummy item
        items = CDSR.objects.filter(cdsr_name=register_name).exclude(
            product_description="Register Created",
            product_category="System",
            product_type="System",
            product_quantity=0,
            single_cost=0,
            total_cost=0,
            remaining_quantity=0
        )
        
        # Check if register has any real items
        if items.exists():
            messages.error(request, f"Cannot delete register '{register_name}' as it contains items.")
            return redirect('register_management:manage_stock_by_register')
        
        # Delete the register (including the dummy item)
        CDSR.objects.filter(cdsr_name=register_name).delete()
        messages.success(request, f"Register '{register_name}' deleted successfully.")
    return redirect('register_management:manage_stock_by_register')

