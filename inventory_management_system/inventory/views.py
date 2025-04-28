from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from .forms import ItemForm  # Added DEPARTMENT_CHOICES import
from django.db.models import Q, Sum, OuterRef, Subquery, Case, When, Value, BooleanField, Exists, Func, CharField , F, Count
from .models import CDSR, DDSR  # ✅ CDSR Model Import
from .decorators import role_required
from django.core.paginator import Paginator
from django.utils.timezone import now
from datetime import timedelta
import csv
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.text import slugify
from datetime import datetime
from babel.numbers import format_decimal


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




# Admin Dashboard View
@login_required
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    # Basic Stats - Using database aggregation
    stats = CDSR.objects.aggregate(
        total_items=Count('cdsr_id'),
        active_items=Count('cdsr_id', filter=Q(writeoff_status__isnull=True)),
        total_value=Sum('total_cost'),
        yearly_value=Sum('total_cost', filter=Q(purchase_year=str(now().year)))
    )
    
    # Department stats using database aggregation
    department_stats = DDSR.objects.aggregate(
        total_allocations=Count('ddsr_id'),
        total_departments=Count('department', distinct=True),
        active_departments=Count('department', distinct=True)
    )
    
    # Current month allocations
    current_month = now().month
    monthly_allocations = DDSR.objects.filter(date_of_receive__month=current_month).count()
    
    # Department Distribution Data - Using database aggregation
    department_data = list(DDSR.objects.values('department')
        .annotate(count=Count('ddsr_id'))
        .values_list('department', 'count')
        .order_by('-count'))
    
    # Ensure we have at least 5 departments for the pie chart colors
    department_labels = [dept for dept, _ in department_data]
    department_data = [count for _, count in department_data]
    
    # Monthly Allocation Data - Using database aggregation
    # Get the last 7 months in chronological order
    last_7_months = []
    monthly_data = []
    
    for i in range(6, -1, -1):
        date = now() - timedelta(days=i*30)
        month_name = date.strftime('%B')
        month_num = date.month
        year = date.year
        
        
        # Get count for this month
        count = DDSR.objects.filter(
            date_of_receive__year=year,
            date_of_receive__month=month_num
        ).count()

        print(count)
        
        last_7_months.append(month_name)
        monthly_data.append(int(count))  # Ensure count is an integer
    
    # Recent Stock Actions - Optimized query with proper action types
    recent_actions = []
    latest_ddsr_entries = DDSR.objects.order_by('-date_of_receive')[:10]
    
    for ddsr in latest_ddsr_entries:
        # Determine action type based on the data
        action_type = 'allocation'  # Default to allocation
        
        # Check if this is a reallocation or deallocation by looking at previous state
        prev_entry = DDSR.objects.filter(
            cdsr_table_id=ddsr.cdsr_table_id,
            department=ddsr.department,
            date_of_receive__lt=ddsr.date_of_receive
        ).order_by('-date_of_receive').first()
        
        if prev_entry:
            if ddsr.accepted_product_quantity < prev_entry.accepted_product_quantity:
                action_type = 'deallocation'
            elif ddsr.accepted_product_quantity > prev_entry.accepted_product_quantity:
                action_type = 'reallocation'
        
        action = {
            'date': ddsr.date_of_receive.strftime('%Y-%m-%d'),
            'item_name': ddsr.product_description,
            'action_type': action_type,
            'department': ddsr.department,
            'quantity': ddsr.accepted_product_quantity,
            'status': 'completed'
        }
        recent_actions.append(action)
    
    context = {
        'total_items': stats['total_items'],
        'active_items': stats['active_items'],
        'total_allocations': department_stats['total_allocations'],
        'monthly_allocations': monthly_allocations,
        'total_departments': department_stats['total_departments'],
        'active_departments': department_stats['active_departments'],
        'total_value': format_decimal(stats['total_value'] or 0, locale='en_IN'),
        'yearly_value': "{:,.2f}".format(stats['yearly_value'] or 0),
        'department_labels': department_labels,
        'department_data': department_data,
        'monthly_labels': last_7_months,
        'monthly_data': monthly_data,
        'recent_actions': recent_actions
    }
    
    # Add debug information to context
    context['debug'] = {
        'monthly_labels': last_7_months,
        'monthly_data': monthly_data,
        'department_labels': department_labels,
        'department_data': department_data
    }
    
    return render(request, "inventory/admin_dashboard.html", context)

# Department Dashboard View
@login_required
@role_required(allowed_roles=['department'])
def department_dashboard(request):
    # Get the department name from the logged-in user
    department_name = request.user.department

    # Get all DDSR entries for this department
    department_items = DDSR.objects.filter(department=department_name)

    # Basic Stats
    total_items = department_items.count()
    total_quantity = department_items.aggregate(Sum('accepted_product_quantity'))['accepted_product_quantity__sum'] or 0
    total_value = sum(float(item.total_cost) for item in department_items) if department_items else 0

    # Calculate percentage changes
    last_month = now() - timedelta(days=30)
    last_year = now() - timedelta(days=365)
    
    new_items = department_items.filter(date_of_receive__gte=last_month).count()
    new_items_percent = round((new_items / total_items * 100) if total_items > 0 else 0, 1)
    
    old_quantity = department_items.filter(date_of_receive__lt=last_month).aggregate(Sum('accepted_product_quantity'))['accepted_product_quantity__sum'] or 0
    quantity_percent = round((total_quantity / (old_quantity + total_quantity) * 100) if (old_quantity + total_quantity) > 0 else 0, 1)
    
    last_year_value = sum(float(item.total_cost) for item in department_items.filter(date_of_receive__lt=last_year)) if department_items else 0
    value_percent = round(((total_value - last_year_value) / last_year_value * 100) if last_year_value > 0 else 0, 1)

    # Recent allocations in last 30 days
    recent_allocations = department_items.filter(date_of_receive__gte=last_month).count()

    # Category Distribution Data
    category_data = []
    category_labels = []
    categories = department_items.values_list('product_category', flat=True).distinct()
    for category in categories:
        count = department_items.filter(product_category=category).count()
        if count > 0:
            category_data.append(count)
            category_labels.append(category)

    # Monthly Trend Data (last 6 months)
    monthly_data = []
    monthly_labels = []
    for i in range(6, -1, -1):
        month_date = now() - timedelta(days=i*30)
        month_name = month_date.strftime('%B')
        monthly_labels.append(month_name)
        count = department_items.filter(
            date_of_receive__year=month_date.year,
            date_of_receive__month=month_date.month
        ).count()
        monthly_data.append(count)

    # Recent Items (last 10 allocations)
    recent_items = department_items.order_by('-date_of_receive')[:10]

    context = {
        'department_name': department_name,
        'total_items': total_items,
        'total_quantity': total_quantity,
        'total_value': format_decimal(total_value , locale='en_IN'),
        'recent_allocations': recent_allocations,
        'new_items_percent': new_items_percent,
        'quantity_percent': quantity_percent,
        'value_percent': value_percent,
        'category_labels': category_labels,
        'category_data': category_data,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'recent_items': recent_items,
    }

    return render(request, "inventory/department_dashboard.html", context)


@login_required
@role_required(allowed_roles=['admin'])
def add_item(request):
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Item added successfully!")
            return redirect_with_no_cache("inventory:inventory_list")
    else:
        form = ItemForm()
    return render(request, "inventory/add_item.html", {"form": form})


@login_required
@role_required(allowed_roles=['admin'])
def inventory_list(request):
    items_list = CDSR.objects.all()

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
        response['Content-Disposition'] = f'attachment; filename="inventory_{timestamp}.csv"'
        
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
        "sort_by": request.GET.get("sort_by", ""),
        "order": request.GET.get("order", "asc"),
        "filter_fields": filter_fields,
        "filter_values": filter_values,
        "from_date": from_date,
        "to_date": to_date
    }

    return render(request, "inventory/inventory_list.html", context)

@login_required
@role_required(allowed_roles=['department'])
def department_inventory_list(request):
    # Get the department name from the logged-in user
    department_name = request.user.department
    
    # Get all DDSR entries for this department
    items_list = DDSR.objects.filter(department=department_name)
    fields = [field.name for field in DDSR._meta.fields]

    # Date Range Filter
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if from_date:
        items_list = items_list.filter(date_of_receive__gte=from_date)
    if to_date:
        items_list = items_list.filter(date_of_receive__lte=to_date)

    # Sorting Logic
    sort_by = request.GET.get("sort_by", "ddsr_id")
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
        response['Content-Disposition'] = f'attachment; filename="{slugify(department_name)}_inventory_{timestamp}.csv"'
        
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
        "department_name": department_name,
        "sort_by": request.GET.get("sort_by", ""),
        "order": request.GET.get("order", "asc"),
        "filter_fields": filter_fields,
        "filter_values": filter_values,
        "from_date": from_date,
        "to_date": to_date
    }

    return render(request, "inventory/department_inventory_list.html", context)

@login_required
@role_required(allowed_roles=['admin'])
def edit_item(request, cdsr_id):
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
                return render(request, "inventory/edit_item.html", {
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
            return redirect_with_no_cache("inventory:inventory_list")
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
    
    return render(request, "inventory/edit_item.html", context)

@login_required
@role_required(allowed_roles=['admin'])
def delete_item(request, cdsr_id):
    cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
    
    if request.method == "POST":
        allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
        if allocations.exists():
            messages.error(request, "Cannot delete item with existing allocations. Please deallocate first.")
            return redirect_with_no_cache("inventory:inventory_list")
            
        cdsr_item.delete()
        messages.success(request, "Item deleted successfully!")
        return redirect_with_no_cache("inventory:inventory_list")
    
    allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
    total_allocated = allocations.aggregate(total=Sum('accepted_product_quantity'))['total'] or 0
    
    context = {
        "cdsr_item": cdsr_item,
        "allocations": allocations,
        "total_allocated": total_allocated
    }
    
    return render(request, "inventory/delete_item.html", context)

