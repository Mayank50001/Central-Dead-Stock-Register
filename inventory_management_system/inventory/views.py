from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DepartmentUserCreationForm, ItemForm  # ✅ Added ItemForm
from django.db.models import Q
from accounts.models import CustomUser
from .models import CDSR , DDSR  # ✅ CDSR Model Import
from .decorators import role_required
from django.core.paginator import Paginator


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

    # Checking which CDSR items are allocated in DDSR
    for item in cdsr_items:
        allocated_item = DDSR.objects.filter(cdsr_table_id=item.cdsr_id).first()
        item.is_allocated = allocated_item is not None  # True if allocated
        item.allocated_department = allocated_item.department if allocated_item else None


    # ✅ Pagination
    paginator = Paginator(cdsr_items, 500)  # 50 items per page
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

    if request.method == "POST":
        ddsr_no = request.POST.get("ddsr_no")
        ddsr_pg_no = request.POST.get("ddsr_pg_no")
        department = request.POST.get("department")

        # Creating DDSR entry
        DDSR.objects.create(
            cdsr_table_id=cdsr_item.cdsr_id,
            cdsr_no=cdsr_item.cdsr_no,
            cdsr_pg_no=cdsr_item.cdsr_pg_no,
            cdsr_name=cdsr_item.cdsr_name,
            product_quantity=cdsr_item.product_quantity,
            product_category=cdsr_item.product_category,
            product_description=cdsr_item.product_description,
            department=department,
            ddsr_no=ddsr_no,
            ddsr_pg_no=ddsr_pg_no,
        )

        return redirect("inventory:cdsr_allocation_list")

    return render(request, "inventory/allocate_form.html", {"cdsr_item": cdsr_item})

def bulk_allocate_confirm(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")

        if not selected_ids:
            messages.warning(request, "No items selected for allocation.")
            return redirect("inventory:allocation_list")

        selected_items = CDSR.objects.filter(cdsr_id__in=selected_ids)
        return render(request, "inventory/bulk_allocate_confirm.html", {"selected_items": selected_items})

    return redirect("inventory:allocation_list")


def bulk_allocate(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        department = request.POST.get("department")

        if not selected_ids:
            messages.warning(request, "No items selected for allocation.")
            return redirect("inventory:allocation_list")

        if not department:
            messages.warning(request, "Please select a department.")
            return redirect("inventory:bulk_allocate_confirm")

        for cdsr_id in selected_ids:
            cdsr_item = get_object_or_404(CDSR, cdsr_id=cdsr_id)
            if not DDSR.objects.filter(cdsr_table_id=cdsr_id).exists():  
                DDSR.objects.create(
                    cdsr_no=cdsr_item.cdsr_no,
                    cdsr_page_no=cdsr_item.cdsr_pg_no,
                    cdsr_name=cdsr_item.cdsr_name,
                    product_category=cdsr_item.product_category,
                    product_description=cdsr_item.product_description,
                    product_quantity=cdsr_item.product_quantity,
                    product_type=cdsr_item.product_type,
                    supplier_name=cdsr_item.supplier,
                    total_cost=cdsr_item.total_cost,
                    year_of_buy=cdsr_item.purchase_year,
                    cdsr_table_id=cdsr_id,  
                    department=department  # ✅ Assign selected department
                )

        messages.success(request, f"Selected items allocated to {department} successfully.")
        return redirect("inventory:cdsr_allocation_list")  

    return redirect("inventory:cdsr_allocation_list")  
