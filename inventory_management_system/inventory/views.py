from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DepartmentUserCreationForm, ItemForm  # ✅ Added ItemForm
from django.db.models import Q , Sum
from accounts.models import CustomUser
from .models import CDSR , DDSR  # ✅ CDSR Model Import
from .decorators import role_required
from django.core.paginator import Paginator
from django.utils.timezone import now


@login_required
@role_required(allowed_roles=['admin'])
def add_department_user(request):
    if request.method == "POST":
        form = DepartmentUserCreationForm(request.POST)
        if form.is_valid():
            department_user = form.save(commit=False)
            department_user.set_password(form.cleaned_data["password"])  # Hash the password
            department_user.role = "department"  # ✅ Ensure role is department
            department_user.department = form.cleaned_data["department"]  # ✅ Assign department
            department_user.save()
            return redirect("inventory:admin_dashboard")
    else:
        form = DepartmentUserCreationForm()
    return render(request, "inventory/add_department_user.html", {"form": form})


# Admin Dashboard View
@login_required
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    return render(request, "inventory/admin_dashboard.html")


# Department Dashboard View
@login_required
@role_required(allowed_roles=['department'])
def department_dashboard(request):
    return render(request, "inventory/department_dashboard.html")


@login_required
@role_required(allowed_roles=['admin'])
def add_item(request):
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Item added successfully!")
            return redirect("inventory:inventory_list")
    else:
        form = ItemForm()
    return render(request, "inventory/add_item.html", {"form": form})


@login_required
@role_required(allowed_roles=['admin'])
def inventory_list(request):
    items_list = CDSR.objects.all()

    fields = [field.name for field in CDSR._meta.fields]  # ✅ Fetch All Column Names

    # ✅ Sorting Logic
    sort_by = request.GET.get("sort_by", "cdsr_id")  # Default sorting field
    order = request.GET.get("order", "asc")  # Default order is ascending
    if order == "desc":
        sort_by = f"-{sort_by}"
    items_list = items_list.order_by(sort_by)

    # ✅ Filtering Logic
    filter_queries = Q()
    filter_fields = request.GET.getlist("filter_field")
    filter_values = request.GET.getlist("filter_value")

    for field, value in zip(filter_fields, filter_values):
        if field and value:
            filter_queries &= Q(**{f"{field}__icontains": value})

    items_list = items_list.filter(filter_queries)

    # ✅ Pagination
    paginator = Paginator(items_list, 50)  # 50 items per page
    page_number = request.GET.get("page")
    items = paginator.get_page(page_number)

    return render(request, "inventory/inventory_list.html", {
        "items": items,
        "fields": fields,
        "sort_by": request.GET.get("sort_by", ""),
        "order": request.GET.get("order", "asc"),
        "filter_fields": filter_fields,
        "filter_values": filter_values
    })


@login_required
@role_required(allowed_roles=['admin'])
def cdsr_allocation_list(request):
    # Fetching all CDSR items
    cdsr_items = CDSR.objects.all()
    fields = [field.name for field in CDSR._meta.fields]  # ✅ Fetch All Column Names

    # ✅ Filtering Logic
    filter_queries = Q()
    filter_fields = request.GET.getlist("filter_field")
    filter_values = request.GET.getlist("filter_value")

    for field, value in zip(filter_fields, filter_values):
        if field and value:
            filter_queries &= Q(**{f"{field}__icontains": value})

    cdsr_items = cdsr_items.filter(filter_queries)

    # Checking which CDSR items are fully allocated in DDSR
    for item in cdsr_items:
        is_fully_allocated = item.remaining_quantity == 0  # Fully allocated if no stock left
        item.is_allocated = is_fully_allocated  # True only if remaining_quantity is 0

        # 🔹 Fetch all departments and their allocated quantity for this item
        allocated_data = DDSR.objects.filter(cdsr_table_id=item.cdsr_id).values('department').annotate(total_allocated=Sum('accepted_product_quantity'))
        
        # Add has_allocations attribute
        item.has_allocations = allocated_data.exists()
        
        # 🔹 Format department list as: "Computer Science (10), Mechanical (5)"
        item.allocated_department = ', '.join([f"{entry['department']} ({entry['total_allocated']})" for entry in allocated_data]) if allocated_data else None

    # ✅ 🔥 New Filtering Logic
    allocated_filter = request.GET.get("allocated_filter")  # ✅ Get Filter Type
    if allocated_filter == "allocated":
        cdsr_items = [item for item in cdsr_items if item.is_allocated]
    elif allocated_filter == "unallocated":
        cdsr_items = [item for item in cdsr_items if not item.is_allocated]

    # ✅ Pagination
    paginator = Paginator(cdsr_items, 25)  # 50 items per page
    page_number = request.GET.get("page")
    cdsr_item_list = paginator.get_page(page_number)

    return render(request, "inventory/allocation_list.html", {
        "cdsr_items": cdsr_item_list,
        "fields": fields,
        "filter_fields": filter_fields,
        "filter_values": filter_values
        })


@login_required
@role_required(allowed_roles=['admin'])
def allocate_form(request, cdsr_id):
    cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
    # Get all existing allocations
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
            return redirect("inventory:allocate_form", cdsr_id=cdsr_id)
        
        elif allocation_type == "reallocation":
            total_reallocated = 0
            # Handle each selected allocation
            for alloc_id in reallocation_from:
                realloc_qty = int(request.POST.get(f"reallocation_quantity_{alloc_id}", 0))
                if realloc_qty > 0:
                    existing_alloc = DDSR.objects.get(ddsr_id=alloc_id)
                    
                    # Validate reallocation quantity
                    if realloc_qty > existing_alloc.accepted_product_quantity:
                        messages.error(request, f"Cannot reallocate more than allocated quantity from {existing_alloc.department}")
                        return redirect("inventory:allocate_form", cdsr_id=cdsr_id)
                    
                    total_reallocated += realloc_qty
                    
                    # If taking partial quantity, update existing allocation
                    if realloc_qty < existing_alloc.accepted_product_quantity:
                        existing_alloc.accepted_product_quantity -= realloc_qty
                        existing_alloc.total_cost = existing_alloc.accepted_product_quantity * existing_alloc.cost_unit
                        existing_alloc.save()
                    else:
                        # If taking all quantity, delete the allocation
                        existing_alloc.delete()

            # Validate total reallocation
            if total_quantity > total_reallocated:
                messages.error(request, "Cannot reallocate more than the selected quantities.")
                return redirect("inventory:allocate_form", cdsr_id=cdsr_id)
            
            # Update CDSR remaining quantity
            cdsr_item.remaining_quantity += total_reallocated

        # Create DDSR entries for each department
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

        # Update remaining quantity in CDSR
        if allocation_type == "new":
            cdsr_item.remaining_quantity -= total_quantity
        else:  # reallocation
            cdsr_item.remaining_quantity = (cdsr_item.remaining_quantity - total_quantity)
        
        cdsr_item.save()

        messages.success(request, "CDSR item allocated successfully to multiple departments.")
        return redirect("inventory:cdsr_allocation_list")

    context = {
        "cdsr_item": cdsr_item,
        "existing_allocations": existing_allocations,
        "true_remaining": true_remaining,
        "total_allocated": total_allocated
    }
    return render(request, "inventory/allocate_form.html", context)


def bulk_allocate_confirm(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")

        if not selected_ids:
            messages.warning(request, "No items selected for allocation.")
            return redirect("inventory:cdsr_allocation_list")

        selected_items = CDSR.objects.filter(cdsr_id__in=selected_ids)
        return render(request, "inventory/bulk_allocate_confirm.html", {"selected_items": selected_items})

    return redirect("inventory:cdsr_allocation_list")


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
            return redirect("inventory:cdsr_allocation_list")

        if not department:
            messages.warning(request, "Please select a department.")
            return redirect("inventory:bulk_allocate_confirm")

        for cdsr_id, quantity, ddsr_no, ddsr_pg_no in zip(selected_ids, accepted_quantities, ddsr_nos, ddsr_pg_nos):
            cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
            quantity = int(quantity)

            # Handle existing allocation
            existing_allocation = DDSR.objects.filter(cdsr_table_id=cdsr_id).first()
            if existing_allocation:
                cdsr_item.remaining_quantity += existing_allocation.accepted_product_quantity
                existing_allocation.delete()

            # Check if allocation is valid
            if quantity > cdsr_item.remaining_quantity:
                messages.error(request, f"Cannot allocate {quantity} units for {cdsr_item.product_description}. Only {cdsr_item.remaining_quantity} available.")
                continue

            DDSR.objects.create(
                cdsr_name=cdsr_item.cdsr_name,
                cdsr_no=cdsr_item.cdsr_no,
                cdsr_page_no=cdsr_item.cdsr_pg_no,
                cdsr_table_id=cdsr_item.cdsr_id,
                cost_unit = cdsr_item.single_cost,
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

            # Update remaining quantity
            cdsr_item.remaining_quantity -= quantity
            cdsr_item.save()

        messages.success(request, f"Selected items allocated to {department} successfully.")
        return redirect("inventory:cdsr_allocation_list")

    return redirect("inventory:cdsr_allocation_list")  


@login_required
@role_required(allowed_roles=['admin'])
def deallocate_form(request, cdsr_id):
    cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
    existing_allocations = DDSR.objects.filter(cdsr_table_id=cdsr_id)
    total_allocated = sum(alloc.accepted_product_quantity for alloc in existing_allocations)

    if request.method == "POST":
        selected_allocations = request.POST.getlist("deallocate_from")
        dealloc_quantities = []
        
        # Collect quantities to deallocate
        for alloc_id in selected_allocations:
            qty = int(request.POST.get(f"deallocation_quantity_{alloc_id}", 0))
            if qty > 0:
                dealloc_quantities.append((alloc_id, qty))

        if not dealloc_quantities:
            messages.error(request, "Please select at least one allocation to deallocate.")
            return redirect("inventory:deallocate_form", cdsr_id=cdsr_id)

        # Process deallocation
        for alloc_id, qty in dealloc_quantities:
            allocation = DDSR.objects.get(ddsr_id=alloc_id)
            
            if qty > allocation.accepted_product_quantity:
                messages.error(request, f"Cannot deallocate more than allocated quantity from {allocation.department}")
                continue

            if qty == allocation.accepted_product_quantity:
                # If deallocating entire quantity, delete the allocation
                allocation.delete()
            else:
                # If partial deallocation, update the allocation
                allocation.accepted_product_quantity -= qty
                allocation.total_cost = allocation.accepted_product_quantity * allocation.cost_unit
                allocation.save()

            # Update CDSR remaining quantity
            cdsr_item.remaining_quantity += qty
            cdsr_item.save()

        messages.success(request, "Successfully deallocated selected quantities.")
        return redirect("inventory:cdsr_allocation_list")

    context = {
        "cdsr_item": cdsr_item,
        "existing_allocations": existing_allocations,
        "total_allocated": total_allocated
    }
    return render(request, "inventory/deallocate_form.html", context)

@login_required
@role_required(allowed_roles=['admin'])
def bulk_deallocate_confirm(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        if not selected_ids:
            messages.warning(request, "No items selected for deallocation.")
            return redirect("inventory:cdsr_allocation_list")

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
            return redirect("inventory:cdsr_allocation_list")

        return render(request, "inventory/bulk_deallocate_confirm.html", {
            "items_with_allocations": items_with_allocations
        })

    return redirect("inventory:cdsr_allocation_list")

@login_required
@role_required(allowed_roles=['admin'])
def bulk_deallocate(request):
    if request.method == "POST":
        deallocations = {}
        
        # Collect all deallocation data from the form
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
            return redirect("inventory:cdsr_allocation_list")

        # Process deallocations
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
        return redirect("inventory:cdsr_allocation_list")

    return redirect("inventory:cdsr_allocation_list")

