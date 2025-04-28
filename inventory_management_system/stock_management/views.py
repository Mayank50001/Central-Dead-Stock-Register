from django.shortcuts import render , get_object_or_404 , redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, OuterRef, Subquery, Case, When, Value, BooleanField, Exists, Func, CharField , F
from inventory.decorators import role_required
from inventory.models import CDSR, DDSR
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.contrib import messages
# Create your views here.

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

from django.db.models import Value, F, CharField
from django.db.models.functions import Concat

class GroupConcat(Func):
    function = 'GROUP_CONCAT'
    template = "%(function)s(%(distinct)s%(expressions)s SEPARATOR %(separator)s)"
    output_field = CharField()

    def __init__(self, expression, distinct=False, separator=', ', **extra):
        super().__init__(expression, **extra)
        self.extra['distinct'] = 'DISTINCT ' if distinct else ''
        self.extra['separator'] = f"'{separator}'"

@login_required
@role_required(allowed_roles=['admin'])
def cdsr_allocation_list(request):
    # Get filter fields and values from the request
    filter_fields = request.GET.getlist("filter_field")
    filter_values = request.GET.getlist("filter_value")

    # Initial QuerySet: Start with CDSR filtering and annotations
    filter_queries = Q()
    for field, value in zip(filter_fields, filter_values):
        if field and value:
            filter_queries &= Q(**{f"{field}__icontains": value})

    # Efficient query without select_related (since there's no ForeignKey relationship)
    cdsr_items = CDSR.objects.filter(filter_queries)

    # Add annotations for 'is_fully_allocated' and 'allocated_departments'
    cdsr_items = cdsr_items.annotate(
    is_fully_allocated=Case(
        When(remaining_quantity=0, then=Value(True)),
        default=Value(False),
        output_field=BooleanField(),
    ),
    allocated_departments=Subquery(
        DDSR.objects.filter(cdsr_table_id=OuterRef('cdsr_id'))
        .values('cdsr_table_id')
        .annotate(
            departments=GroupConcat(
                Concat(F('department'), Value(' ('), F('accepted_product_quantity'), Value(')')),
                distinct=True,
                separator=', '
            )
        )
        .values('departments')[:1]
    ),
    has_allocations=Exists(
        DDSR.objects.filter(cdsr_table_id=OuterRef('cdsr_id'))
    ),
    )   
    
    # Handle the allocation filter condition (allocated/unallocated)
    allocated_filter = request.GET.get("allocated_filter")
    if allocated_filter == "allocated":
        cdsr_items = cdsr_items.filter(is_fully_allocated=True)
    elif allocated_filter == "unallocated":
        cdsr_items = cdsr_items.filter(is_fully_allocated=False)

    # Pagination: Apply pagination after filtering and annotating
    paginator = Paginator(cdsr_items, 50)
    page_number = request.GET.get("page")
    cdsr_item_list = paginator.get_page(page_number)

    # Pass the necessary context to the template
    return render(request, "stock_management/allocation_list.html", {
        "cdsr_items": cdsr_item_list,
        "fields": [field.name for field in CDSR._meta.fields],  # Get all column names
        "filter_fields": filter_fields,
        "filter_values": filter_values,
        "allocated_filter": allocated_filter,
    })


@login_required
@role_required(allowed_roles=['admin'])
def allocate_form(request, cdsr_id):
    cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
    existing_allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
    total_allocated = sum(alloc.accepted_product_quantity for alloc in existing_allocations)
    true_remaining = cdsr_item.product_quantity - total_allocated

    if request.method == "POST":
        departments = request.POST.getlist("departments[]")
        ddsr_nos = request.POST.getlist("ddsr_nos[]")
        ddsr_pg_nos = request.POST.getlist("ddsr_pg_nos[]")
        quantities = [int(qty) for qty in request.POST.getlist("quantities[]")]
        allocation_type = request.POST.get("allocation_type")
        reallocation_from = request.POST.getlist("reallocation_from")

        total_quantity = sum(quantities)

        if allocation_type == "new" and total_quantity > true_remaining:
            messages.error(request, "Cannot allocate more than available remaining quantity.")
            return redirect_with_no_cache("stock_management:allocate_form", cdsr_id=cdsr_id)
        
        elif allocation_type == "reallocation":
            total_reallocated = 0
            for alloc_id in reallocation_from:
                realloc_qty = int(request.POST.get(f"reallocation_quantity_{alloc_id}", 0))
                if realloc_qty > 0:
                    existing_alloc = DDSR.objects.get(ddsr_id=alloc_id)
                    
                    if realloc_qty > existing_alloc.accepted_product_quantity:
                        messages.error(request, f"Cannot reallocate more than allocated quantity from {existing_alloc.department}")
                        return redirect_with_no_cache("inventory:allocate_form", cdsr_id=cdsr_id)
                    
                    total_reallocated += realloc_qty
                    
                    if realloc_qty < existing_alloc.accepted_product_quantity:
                        existing_alloc.accepted_product_quantity -= realloc_qty
                        existing_alloc.total_cost = existing_alloc.accepted_product_quantity * existing_alloc.cost_unit
                        existing_alloc.save()
                    else:
                        existing_alloc.delete()

            if total_quantity > total_reallocated:
                messages.error(request, "Cannot reallocate more than the selected quantities.")
                return redirect_with_no_cache("inventory:allocate_form", cdsr_id=cdsr_id)
            
            cdsr_item.remaining_quantity += total_reallocated

        for department, ddsr_no, ddsr_pg_no, quantity in zip(departments, ddsr_nos, ddsr_pg_nos, quantities):
            DDSR.objects.create(
                cdsr_name=cdsr_item.cdsr_name,
                cdsr_no=cdsr_item.cdsr_no,
                cdsr_page_no=cdsr_item.cdsr_pg_no,
                cdsr_table_id=cdsr_item.cdsr_id,
                cost_unit=cdsr_item.single_cost,
                date_of_receive=now(),
                ddsr_no=ddsr_no,
                ddsr_pg_no=ddsr_pg_no,
                department=department,
                product_quantity=cdsr_item.product_quantity,
                product_category=cdsr_item.product_category,
                product_description=cdsr_item.product_description,
                product_type=cdsr_item.product_type,
                accepted_product_quantity=quantity,
                supplier_name=cdsr_item.supplier,
                total_cost=quantity * cdsr_item.single_cost,
                year_of_buy=cdsr_item.purchase_year
            )

        if allocation_type == "new":
            cdsr_item.remaining_quantity -= total_quantity
        else:  # reallocation
            cdsr_item.remaining_quantity = (cdsr_item.remaining_quantity - total_quantity)
        
        cdsr_item.save()

        messages.success(request, "CDSR item allocated successfully to multiple departments.")
        return redirect_with_no_cache("stock_management:cdsr_allocation_list")

    context = {
        "cdsr_item": cdsr_item,
        "existing_allocations": existing_allocations,
        "true_remaining": true_remaining,
        "total_allocated": total_allocated
    }
    return render(request, "stock_management/allocate_form.html", context)


def bulk_allocate_confirm(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")

        if not selected_ids:
            messages.warning(request, "No items selected for allocation.")
            return redirect("stock_management:cdsr_allocation_list")

        selected_items = CDSR.objects.filter(cdsr_id__in=selected_ids)
        return render(request, "stock_managemen/bulk_allocate_confirm.html", {"selected_items": selected_items})

    return redirect("stock_management:cdsr_allocation_list")


@login_required
@role_required(allowed_roles=['admin'])
def bulk_allocate(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        department = request.POST.get("department")
        accepted_quantities = request.POST.getlist("accepted_product_quantity")
        ddsr_nos = request.POST.getlist("ddsr_no")
        ddsr_pg_nos = request.POST.getlist("ddsr_pg_no")

        if not selected_ids:
            messages.warning(request, "No items selected for allocation.")
            return redirect_with_no_cache("stock_management:cdsr_allocation_list")

        if not department:
            messages.warning(request, "Please select a department.")
            return redirect_with_no_cache("stock_management:bulk_allocate_confirm")

        for cdsr_id, quantity, ddsr_no, ddsr_pg_no in zip(selected_ids, accepted_quantities, ddsr_nos, ddsr_pg_nos):
            cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
            quantity = int(quantity)

            existing_allocation = DDSR.objects.filter(cdsr_table_id=cdsr_id).first()
            if existing_allocation:
                cdsr_item.remaining_quantity += existing_allocation.accepted_product_quantity
                existing_allocation.delete()

            if quantity > cdsr_item.remaining_quantity:
                messages.error(request, f"Cannot allocate {quantity} units for {cdsr_item.product_description}. Only {cdsr_item.remaining_quantity} available.")
                continue

            DDSR.objects.create(
                cdsr_name=cdsr_item.cdsr_name,
                cdsr_no=cdsr_item.cdsr_no,
                cdsr_page_no=cdsr_item.cdsr_pg_no,
                cdsr_table_id=cdsr_item.cdsr_id,
                cost_unit=cdsr_item.single_cost,
                date_of_receive=now(),
                ddsr_no=ddsr_no,
                ddsr_pg_no=ddsr_pg_no,
                department=department,
                product_quantity=cdsr_item.product_quantity,
                product_category=cdsr_item.product_category,
                product_description=cdsr_item.product_description,
                product_type=cdsr_item.product_type,
                accepted_product_quantity=quantity,
                supplier_name=cdsr_item.supplier,
                total_cost=quantity * cdsr_item.single_cost,
                year_of_buy=cdsr_item.purchase_year
            )

            cdsr_item.remaining_quantity -= quantity
            cdsr_item.save()

        messages.success(request, f"Selected items allocated to {department} successfully.")
        return redirect_with_no_cache("stock_management:cdsr_allocation_list")

    return redirect_with_no_cache("stock_management:cdsr_allocation_list")  


@login_required
@role_required(allowed_roles=['admin'])
def deallocate_form(request, cdsr_id):
    cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
    existing_allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
    total_allocated = sum(alloc.accepted_product_quantity for alloc in existing_allocations)

    if request.method == "POST":
        selected_allocations = request.POST.getlist("deallocate_from")
        dealloc_quantities = []
        
        for alloc_id in selected_allocations:
            qty = int(request.POST.get(f"deallocation_quantity_{alloc_id}", 0))
            if qty > 0:
                dealloc_quantities.append((alloc_id, qty))

        if not dealloc_quantities:
            messages.error(request, "Please select at least one allocation to deallocate.")
            return redirect_with_no_cache("stock_management:deallocate_form", cdsr_id=cdsr_id)

        for alloc_id, qty in dealloc_quantities:
            allocation = DDSR.objects.get(ddsr_id=alloc_id)
            
            if qty > allocation.accepted_product_quantity:
                messages.error(request, f"Cannot deallocate more than allocated quantity from {allocation.department}")
                continue

            if qty == allocation.accepted_product_quantity:
                allocation.delete()
            else:
                allocation.accepted_product_quantity -= qty
                allocation.total_cost = allocation.accepted_product_quantity * allocation.cost_unit
                allocation.save()

            cdsr_item.remaining_quantity += qty
            cdsr_item.save()

        messages.success(request, "Successfully deallocated selected quantities.")
        return redirect_with_no_cache("stock_management:cdsr_allocation_list")

    context = {
        "cdsr_item": cdsr_item,
        "existing_allocations": existing_allocations,
        "total_allocated": total_allocated
    }
    return render(request, "stock_management/deallocate_form.html", context)

@login_required
@role_required(allowed_roles=['admin'])
def bulk_deallocate_confirm(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        if not selected_ids:
            messages.warning(request, "No items selected for deallocation.")
            return redirect("stock_management:cdsr_allocation_list")

        items_with_allocations = []
        for cdsr_id in selected_ids:
            cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
            allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
            if allocations.exists():
                items_with_allocations.append({
                    'cdsr_item': cdsr_item,
                    'allocations': allocations
                })

        if not items_with_allocations:
            messages.warning(request, "None of the selected items have any allocations.")
            return redirect("stock_management:cdsr_allocation_list")

        return render(request, "stock_management/bulk_deallocate_confirm.html", {
            "items_with_allocations": items_with_allocations
        })

    return redirect("stock_management:cdsr_allocation_list")

@login_required
@role_required(allowed_roles=['admin'])
def bulk_deallocate(request):
    if request.method == "POST":
        deallocations = {}
        
        for key, value in request.POST.items():
            if key.startswith('deallocation_quantity_'):
                try:
                    alloc_id = key.split('_')[-1]
                    qty = int(value)
                    if qty > 0:
                        deallocations[alloc_id] = qty
                except (ValueError, IndexError):
                    continue

        if not deallocations:
            messages.error(request, "No valid deallocations specified.")
            return redirect_with_no_cache("stock_management:cdsr_allocation_list")

        for alloc_id, qty in deallocations.items():
            try:
                allocation = DDSR.objects.get(ddsr_id=alloc_id)
                cdsr_item = CDSR.objects.get(cdsr_id=allocation.cdsr_table_id)

                if qty > allocation.accepted_product_quantity:
                    messages.error(request, f"Cannot deallocate more than allocated quantity from {allocation.department} for {cdsr_item.cdsr_name}")
                    continue

                if qty == allocation.accepted_product_quantity:
                    allocation.delete()
                else:
                    allocation.accepted_product_quantity -= qty
                    allocation.total_cost = allocation.accepted_product_quantity * allocation.cost_unit
                    allocation.save()

                cdsr_item.remaining_quantity += qty
                cdsr_item.save()

            except (DDSR.DoesNotExist, CDSR.DoesNotExist):
                messages.error(request, f"Error processing deallocation for allocation {alloc_id}")
                continue

        messages.success(request, "Successfully processed bulk deallocations.")
        return redirect_with_no_cache("stock_management:cdsr_allocation_list")

    return redirect_with_no_cache("stock_management:cdsr_allocation_list")