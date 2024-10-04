from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pyexpat.errors import messages
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.views import View
from .models import *
from .models import Brand
from django.contrib.auth.hashers import make_password, check_password
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.contrib.sessions.models import Session
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.contrib import messages



from django.db import transaction

from django.utils import timezone

def home(request):
    return render(request, 'IMS_admin/login.html')

def base(request):
    return render(request, 'base/base.html')



def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('uID')
        password = request.POST.get('psw')
        
        try:
            # Check if the user is an Employee
            employee = Employee.objects.get(email=username)
            if check_password(password, employee.password):
                request.session['userid'] = employee.id
                request.session['user_role'] = 'employee'
                request.session['first_name'] = employee.First_name
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password')
                return redirect('admin_login')
        
        except Employee.DoesNotExist:
            messages.error(request, 'Invalid username')
            return redirect('admin_login')
    
    return render(request, 'IMS_Admin/login.html')




def log_out(request):
    try:
        # Clear the session
        request.session.flush()
        messages.success(request, 'Successfully logged out!')
    except KeyError:
        pass
    return redirect('admin_login')

@transaction.atomic
def createOrder(request):
    if request.method == "POST":
        customer_id = request.POST.get('customer_id')
        warehouse_id = request.POST.get('warehouse_id')
        sales_employee_id = request.POST.get('sales_employee_id')
        order_date = request.POST.get('order_date')

        # Fetch customer, sales employee, and warehouse objects
        customer = Customer.objects.get(customer_id=customer_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)
        sales_employee = Employee.objects.get(id=sales_employee_id)

        # Create order instance
        new_order = Order.objects.create(
            customer=customer,
            warehouse=warehouse,
            sales_employee=sales_employee,
            order_date=order_date
        )

        # Process each product in the order
        for i, product_id in enumerate(request.POST.getlist('product[]')):
            product = Product.objects.get(product_id=product_id)
            quantity = int(request.POST.getlist('quantity[]')[i])
            
            # Check and update stock
            stock = Stock.objects.get(product=product, warehouse=warehouse)
            if stock.stock_number < quantity:
                messages.error(request, f"Not enough stock for {product.product_name}.")
                continue  # Skip creating OrderDetail for this product

            stock.stock_number -= quantity
            stock.save()

            # Create OrderDetail
            OrderDetail.objects.create(
                order=new_order,
                product=product,
                quantity=quantity,
                unit_price=float(request.POST.getlist('unit_price[]')[i]),
                discount=float(request.POST.getlist('discount[]')[i]),
                tax_type=request.POST.getlist('tax_type[]')[i],
                tax_rate=float(request.POST.getlist('tax_rate[]')[i])
            )

        return redirect('orders')
    else:
        products = Product.objects.all()
        customers = Customer.objects.all()
        employees = Employee.objects.all()
        warehouses = Warehouse.objects.all()  # Load all warehouses
        return render(request, 'Extra/create_orders.html', {
            'products': products,
            'customers': customers,
            'employees': employees,
            'warehouses': warehouses  # Add warehouses to context
        })


from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, Product, Customer, Warehouse, OrderDetail

def edit_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        # Process the form data
        customer_id = request.POST.get('customer_id')
        warehouse_id = request.POST.get('warehouse_id')
        order_date = request.POST.get('order_date')
        invoice_generated = request.POST.get('invoice_generated') == 'on'
        
        # Update order fields
        if customer_id:
            customer = get_object_or_404(Customer, customer_id=customer_id)
            order.customer = customer
        order.warehouse_id = warehouse_id
        order.order_date = order_date
        order.invoice_generated = invoice_generated
        order.save()

        # Process order details
        for key in request.POST:
            if key.startswith('product_'):
                detail_id = key.split('_')[1]
                product_id = request.POST.get(f'product_{detail_id}')
                description = request.POST.get(f'description_{detail_id}')
                quantity = request.POST.get(f'quantity_{detail_id}')
                unit_price = request.POST.get(f'unit_price_{detail_id}')
                discount = request.POST.get(f'discount_{detail_id}')
                tax_type = request.POST.get(f'tax_type_{detail_id}')
                tax_rate = request.POST.get(f'tax_rate_{detail_id}')
                subtotal = request.POST.get(f'subtotal_{detail_id}')
                total = request.POST.get(f'total_{detail_id}')
                
                # Fetch or create the order detail item
                order_detail, created = OrderDetail.objects.get_or_create(order=order, id=detail_id)

                # Update order detail fields
                order_detail.product_id = product_id
                order_detail.description = description
                order_detail.quantity = quantity
                order_detail.unit_price = unit_price
                order_detail.discount = discount
                order_detail.tax_type = tax_type
                order_detail.tax_rate = tax_rate

                # Calculate subtotal and total
                subtotal_value = float(quantity) * float(unit_price)
                subtotal_value -= (subtotal_value * float(discount) / 100)
                subtotal_value += (subtotal_value * float(tax_rate) / 100)

                order_detail.subtotal = subtotal_value
                order_detail.total = subtotal_value

                order_detail.save()

        return redirect('orders')

    # Get products, customers, and warehouses for the dropdowns
    products = Product.objects.all()
    customers = Customer.objects.all()
    warehouses = Warehouse.objects.all()

    order_details = OrderDetail.objects.filter(order=order)

    context = {
        'order': order,
        'products': products,
        'customers': customers,
        'warehouses': warehouses,
        'order_details': order_details
    }

    return render(request, 'IMS_admin/edit_order.html', context)



def generate_invoice(request):
    company = Company_details.objects.get(id=1)
    customers = Customer.objects.all()
    customer_data = [{
        'id': customer.customer_id, 
        'name': f"{customer.first_name}", 
        'address': customer.address, 
        'phone': customer.mobile_no
    } for customer in customers]
    
    ord = Order.objects.filter(invoice_generated=False)
    order_data = [{
        'id': order.id, 
        'customer_id': order.customer.customer_id,
        'invoice_generated':order.invoice_generated,
        'details': [{
            'product': detail.product.product_name, 
            'description': detail.product.description, 
            'quantity': float(detail.quantity), 
            'unit_price': float(detail.product.selling_price),
            'tax_rate': float(detail.tax_rate), 
            'tax_type': detail.tax_type,
            'discount':float(detail.discount),
            'tax_amt':float(detail.tax_amount()),
            'sub_total':float(detail.net_amount()),
            'total':float(detail.total_amount()),
            
        } for detail in OrderDetail.objects.filter(order=order)]
    } for order in ord]
    
    context = {
        'customer': json.dumps(customer_data),
        'order': json.dumps(order_data),
        'company': company
    }
    return render(request, 'IMS_admin/invoice11.html', context)



def add_products(request):
    if request.method == "POST":
        productid = request.POST.get('product_id')
        category = request.POST.get('category_name')
        productname = request.POST.get('product_name')
        sku = request.POST.get('sku')
        unit = request.POST.get('unit')
        weight = request.POST.get('weight')
        weightunit = request.POST.get('weightUnit')
        length = request.POST.get('length')
        width = request.POST.get('width')
        height = request.POST.get('height')
        dimunit = request.POST.get('dimensionUnit')
        costprice = request.POST.get('cost_price')
        sellingprice = request.POST.get('selling_price')
        supplier_name = request.POST.get('supplier_name')
        brand = request.POST.get('brand_name')
        hsn = request.POST.get('hsn')
        image = request.FILES.get('image')
        description = request.POST.get('description')
        
        category=Category.objects.get(name=category)
        brand=Brand.objects.get(name=brand)
        man=Supplier.objects.get(id=supplier_name)
        newProduct = Product(
            product_id=productid,
            category=category,
            product_name=productname,
            sku=sku,
            unit=unit,
            weight=weight,
            weight_unit=weightunit,
            length=length,
            width=width,
            height=height,
            dimension_unit=dimunit,
            cost_price=costprice,
            selling_price=sellingprice,
            supplier=man,
            brand=brand,
            hsn_code=hsn,
            image=image,
            description=description,
        )
        newProduct.save()
        return redirect('products')
    else:
        category = Category.objects.all()
        brand = Brand.objects.all()
        manu = Supplier.objects.all()
        context = {
            'manu': manu,
            'category': category,
            'brand': brand,
        }
        return render(request, 'IMS_admin/productform.html', context)

def add_department(request):
    if request.method == "POST":
        dept_id = request.POST.get('new_department_id')
        dept_name = request.POST.get('new_department_name')

        newDepartment = Department(
            id=dept_id,
            name=dept_name
        )
        newDepartment.save()
        return redirect('departments')
    else:
        return render(request, 'IMS_admin/department_form.html')


def add_employee(request):
    if request.method == "POST":
        gender = request.POST.get('gender')
        firstname = request.POST.get('first_name')
        lastname = request.POST.get('last_name')
        dob = request.POST.get('date_of_birth')
        email = request.POST.get('email')
        address = request.POST.get('address')
        phone = request.POST.get('phone_num')
        designation = request.POST.get('designation')
        doj = request.POST.get('date_of_join')
        image = request.FILES.get('image')
        dept = request.POST.get('department_name')

        department = Department.objects.get(name=dept)

        newEmployee = Employee(
            gender=gender,
            First_name=firstname,
            last_name=lastname,
            date_of_birth=dob,  
            email=email,
            address=address,
            phone_number=phone,
            designation=designation,
            date_of_joining=doj,
            image=image,
            department=department
        )
        newEmployee.save()
        return redirect('employees')
    else:
        Dept = Department.objects.all()
        context = {
            'departments': Dept
        }
        return render(request, 'IMS_admin/employee.html', context)

def customer_table(request):
    cust=Customer.objects.all()
    sales = Employee.objects.filter(department__name="Sales")
    
    context={
        'customers':cust,
        'sales_employee':sales,
    }
    return render(request, 'IMS_Admin/customer_table.html', context)

def assign_sales_employee(request):
    if request.method == 'POST' and 'assign_sales_employee' in request.POST:
        customer_id = request.POST.get('customer_id')
        sales_employee_id = request.POST.get('sales_employee')
        customer = Customer.objects.get(id=customer_id)
        sales_employee = Employee.objects.get(id=sales_employee_id)
        
        customer.sales_employee = sales_employee
        customer.save()
        
        return redirect('customers')
    else:
        return HttpResponse('Method not allowed')

def sales_customer_table(request):
    user_id = request.session.get('User ID')
    print(user_id)

    emp = Employee.objects.get(id=user_id)
    cust = Customer.objects.filter(sales_employee=user_id)
    context = {
        'emp': emp,
        'customers': cust
    }
    return render(request, 'IMS_Admin/customer_table.html', context)


def add_category(request):
    if request.method=="POST":
        cate_name=request.POST.get('Category_name')
        cate_id=request.POST.get('Category_id')
        print(cate_name, cate_id)


        newcategory=Category(
            name=cate_name,
            id=cate_id
        )
        newcategory.save()
        return redirect('category')
    else:
        return render(request, 'IMS_Admin/category_form.html')
  
def add_brand(request):
    if request.method=="POST":
        cate_name=request.POST.get('brand_name')
        cate_id=request.POST.get('brand_id')


        newbrand=Brand(
            name=cate_name,
            id=cate_id
        )
        newbrand.save()
        return redirect('brands')
    else:
        return render(request, 'IMS_Admin/brand_form.html')


def add_Supplier(request):
    if request.method == "POST":
        name = request.POST.get('supplier_name')
        email = request.POST.get('supplier_email')
        contact = request.POST.get('supplier_contact')
        gst = request.POST.get('gstin_number')
        pan = request.POST.get('pan_number')
        address = request.POST.get('supplier_address')
        bank_acc = request.POST.get('bank_account_number')
        ifsc = request.POST.get('ifsc_code')
        bank_name = request.POST.get('bank_name')
        business_type = request.POST.get('business_type')
        business_license = request.POST.get('business_license')
        is_manufacturer = request.POST.get('is_manufacturer') == 'on'

        newSupplier = Supplier(
            name=name,
            email=email,
            contact_number=contact,
            gstin_number=gst,
            pan_number=pan,
            address=address,
            bank_account_number=bank_acc,
            ifsc_code=ifsc,
            bank_name=bank_name,
            business_type=business_type,
            business_license_number=business_license,
            is_manufacturer=is_manufacturer
        )
        newSupplier.save()
        return redirect('suppliers')
    else:
        return render(request, 'IMS_Admin/Supplier.html')




def product_table(request):
    prod=Product.objects.all()
    context={
        'products':prod
    }
    return render(request, 'IMS_Admin/producttable.html', context)


def update_stock(request):
    if request.method == "POST":
        warehouse_id = request.POST.get('warehouse_id')
        supplier_id = request.POST.get('supplier_id')
        brand_id = request.POST.get('brand_id')
        product_id = request.POST.get('product_name')  # Correcting to get product_id
        stock_status_str = request.POST.get('stock_status')
        stock_status = stock_status_str == 'In Stock'
        stock_num = int(request.POST.get('stock_num'))
        stock_min = int(request.POST.get('min_stock'))

        supplier_instance = Supplier.objects.get(pk=supplier_id)
        brand_instance = Brand.objects.get(pk=brand_id)
        warehouse_instance = Warehouse.objects.get(pk=warehouse_id)

        try:
            product_instance = Product.objects.get(product_id=product_id)  # Fetch by product_id
        except Product.DoesNotExist:
            # Handle the error if the product doesn't exist
            messages.error(request, "Product does not exist.")
            return redirect('stockupdate')
        
        new_stock = Stock(
            warehouse=warehouse_instance,
            supplier=supplier_instance,
            brand=brand_instance,
            stock_status=stock_status,
            stock_number=stock_num,
            product=product_instance,
            low_stock_threshold = stock_min
        )
        new_stock.save()

        return redirect('stock')
    else:
        suppliers = Supplier.objects.all()
        products = Product.objects.all()
        brands = Brand.objects.all()
        warehouses = Warehouse.objects.all()
        context = {
            'warehouses':warehouses,
            'suppliers': suppliers,
            'products': products,
            'brands': brands
        }
        return render(request, 'IMS_Admin/stock_update.html', context)

def re_stock(request):
    if request.method == "POST":
        warehouse_id = request.POST.get('warehouse_id')
        employee_id = request.POST.get('employee_id')
        product_id = request.POST.get('product_id')
        purchase_order_id = request.POST.get('purchase_order')
        quantity_added = request.POST.get('quantity_added')
        restock_date = request.POST.get('restocked_on')

        print(warehouse_id, employee_id, product_id, purchase_order_id, quantity_added)

        if not quantity_added.isdigit():
            messages.error(request, "Invalid quantity. Please enter a numeric value.")
            return redirect('re_stock')

        quantity_added = int(quantity_added)
        

        try:
            warehouse = Warehouse.objects.get(pk=warehouse_id)
            employee = Employee.objects.get(pk=employee_id)
            product = Product.objects.get(pk=product_id)
            purchase_order = PurchaseOrder.objects.get(pk=purchase_order_id)

            

            stock, created = Stock.objects.get_or_create(
                warehouse=warehouse,
                product=product,
                defaults={'stock_number': 0}
            )
            print(stock.stock_number)
            stock.stock_number += quantity_added
            stock.save()
            poitem=PurchaseOrderItem.objects.filter(purchase_order=purchase_order.id, product=product.product_id)
            print(poitem)

            Restock.objects.create(
                warehouse=warehouse,
                product=product,
                purchase_order=purchase_order,
                quantity_added=quantity_added,
                restocked_by=employee,
                restocked_on = restock_date
            )
        
            return redirect('stock')
        except:
            return HttpResponse("Error")

    else:
        context = {
            'employees': Employee.objects.all(),
            'products': Product.objects.all(),
            'warehouses': Warehouse.objects.all(),
            'purchase_orders': PurchaseOrder.objects.all(),
        }
        return render(request, 'IMS_Admin/re_stock.html', context)

from django.db.models import Sum

def restock_table(request):
    restock_records = Restock.objects.select_related('purchase_order', 'product', 'warehouse').all()

    # Collecting all restocks and related purchase orders for additional fields
    restock_data = []
    for restock in restock_records:
        purchase_order_item = PurchaseOrderItem.objects.filter(purchase_order=restock.purchase_order, product=restock.product).first()
        if purchase_order_item:
            quantity_ordered = purchase_order_item.quantity
            quantity_received = Restock.objects.filter(purchase_order=restock.purchase_order, product=restock.product).aggregate(total_received=Sum('quantity_added'))['total_received'] or 0
            pending_quantity = quantity_ordered - quantity_received
            
            restock_data.append({
                'restock': restock,
                'quantity_ordered': quantity_ordered,
                'quantity_received': quantity_received,
                'pending_quantity': pending_quantity,
            })

    return render(request, 'IMS_Admin/restock_table.html', {'restock_data': restock_data})




def stock_table(request):
    stocks=Stock.objects.all()
    context={
        'stocks':stocks
    }
    return render(request, 'IMS_Admin/stock_table.html', context)



def employees(request):
    employee=Employee.objects.all()
    context={
        'employees':employee
    }
    return render(request, 'IMS_Admin/employee_table.html', context)



def departments(request):
    depart=Department.objects.all()
    context={
        'departments':depart,
    }
    return render(request, 'IMS_Admin/department_table.html', context)


def suppliers(request):
    supplier=Supplier.objects.all()
    context={
        'supplier':supplier
    }
    return render(request, 'IMS_Admin/suppliers_table.html', context)



def category(request):
    cate=Category.objects.all()
    context={
        'category':cate
    }
    return render(request, 'IMS_Admin/category_table.html', context)



def brands(request):
    brand=Brand.objects.all()
    context={
        'brands':brand
    }
    return render(request, 'IMS_Admin/brand_table.html', context)


def delete_product(request, product_id):
    if request.method=='POST':
        
        prod=Product.objects.get(product_id=product_id)
        prod.delete()
        return redirect('products')


def delete_customer(request, customer_id):
    if request.method=="POST":
        cust=Customer.objects.get(customer_id=customer_id)
        cust.delete()
        return redirect('customers')

def delete_Supplier(request, id):
    if request.method=='POST':
        prod=Supplier.objects.get(id=id)
        prod.delete()
        return redirect('suppliers')

def delete_brand(request, id):
    if request.method=="POST":
        brand=Brand.objects.get(id=id)
        brand.delete()
        return redirect('brands')
    
def delete_order(request, id):
    if request.method=="POST":
        order=Order.objects.get(id=id)
        order.delete()
        return redirect('orders')

def delete_category(request, id):
    if request.method=="POST":
        cate=Category.objects.get(id=id)
        cate.delete()
        return redirect('category')



def delete_employee(request, id):
    if request.method=="POST":
        emp=Employee.objects.get(id=id)
        emp.delete()
        return redirect('employees')

  
def delete_department(request, id):
    if request.method=="POST":
        depart=Department.objects.get(id=id)
        depart.delete()
        return redirect('departments')

def edit_employee(request, employee_id):
    print(employee_id)
    employee = Employee.objects.get(id=employee_id)
    departments = Department.objects.all()
    if request.method == 'POST':
        print(request.POST)
        employee.First_name = request.POST['first_name']
        employee.last_name = request.POST['last_name']
        employee.date_of_birth = request.POST['date_of_birth']
        employee.email = request.POST['email']
        employee.address = request.POST['address']
        employee.phone_number = request.POST['phone_number']
        employee.designation = request.POST['designation']
        employee.date_of_joining = request.POST['date_of_joining']
        employee.gender = request.POST['gender']
        department_id = request.POST['department']
        try:
            department = Department.objects.get(id=department_id)
            employee.department = department
        except Department.DoesNotExist:
            pass
        if 'image' in request.FILES:
            employee.image = request.FILES['image']
        employee.save()
        return redirect('employees')
    else:
        return render(request, 'IMS_Admin/edit_employee.html', {'employee': employee, 'departments': departments})


def order_table(request):
    ord=Order.objects.all()
    print(ord)
    context={
        'order':ord
    }
    return render(request, 'IMS_Admin/order.html', context)

def order_details(request, id):
    order = get_object_or_404(Order, id=id)
    order_details = OrderDetail.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_details': order_details,
    }
    return render(request, 'IMS_Admin/orderhistory.html', context)
   

def create_order(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))

        order = Order.objects.create(customer_id=customer_id)
        
        order_detail = OrderDetail.objects.create(
            order=order,
            product_id=product_id,
            quantity=quantity,
            description="Order Detail Description",
            unit_price=10.0, 
            discount=0.0,     
            tax_type="GST"    
        )
        try:
            product = Stock.objects.get(product_name=order_detail.product.product_name)
            product.stock_number -= order_detail.quantity
            product.save()
        except Stock.DoesNotExist:
            return HttpResponse("Product not found in stock.")

        return HttpResponse("Order created successfully and stock stock updated.")
    else:
        return HttpResponse("Invalid request method. Must be POST.")


def invoice_table(request):
    inv=Invoice.objects.all()
    context={
        'invoices':inv
    }
    return render(request, 'IMS_Admin/invoicetable.html', context)

def delete_invoice(request, id):
    inv=Invoice.objects.select_related('customer').all()
    inv.delete()
    return redirect('invoices')

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification_to_clients(notification):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'notifications_group',
        {
            'type': 'send_notification',
            'notification': notification,
        }
    )


class InvoiceCreateView(View):
    def get(self, request):
        orders = Order.objects.all()
        customers = Customer.objects.all()
        return render(request, 'IMS_Admin/invoice11.html', {'orders': orders, 'customers': customers})

    @transaction.atomic
    def post(self, request):
        order_id = request.POST.get('order_id')
        customer_id = request.POST.get('customer_id') 
        print(customer_id) # Assume this now correctly carries the ID
        invoice_date = request.POST.get('invoice_date')
        due_date = request.POST.get('due_date')
        total_amount = float(request.POST.get('total', 0))

        new_invoice = Invoice.objects.create(
            order_id=Order.objects.get(id=order_id),
            customer = Customer.objects.get(customer_id=customer_id),  # Corrected to use id
            invoice_date=invoice_date,
            due_date=due_date,
            total_amount=total_amount
        )
        ord = Order.objects.get(id=order_id)
        ord.invoice_generated = True
        ord.save()

        items_json = request.POST.get('items')
        items = json.loads(items_json)

        for item in items:
            product = Product.objects.get(product_name=item['product'])
            Invoice_items.objects.create(
                invoice_id=new_invoice,
                product_name=product,
                selling_price=Decimal(item['unit_price']),
                net_amount=Decimal(item['subtotal']),
                quantity=int(item['quantity']),
                description=item['item_description'],
                tax_type=item['tax_type'],
                tax_rate=Decimal(item['tax_rate']),
                discount=Decimal(item['discount'])
            )

        return redirect('invoices')  # Change this to your success URL



def view_invoice(request, id):
    inv = get_object_or_404(Invoice, id=id)
    inv_details = Invoice_items.objects.filter(invoice_id=inv)
    cmp=Company_details.objects.get(id=1)
    cust=inv.customer
    
    context={
        'invoice':inv,
        'invoice_details':inv_details,
        'cmp_details':cmp,
        'customer':cust
    }
    return render(request, 'IMS_Admin/invoicehistory.html', context)

def dashboard(request):
    inv_count=Invoice.objects.all()
    invoice_count=inv_count.count()
    total_revenue=0
    for i in inv_count:
        total_revenue+=i.total_amount
    today = timezone.now().date()
    
    # Get today's invoices
    todays_invoices = Invoice.objects.filter(invoice_date=today)
    todays_sales_count = todays_invoices.count()
    todays_revenue = sum(i.total_amount for i in todays_invoices)
    
    context={
        'invoice_count':invoice_count,
        'total_revenue':total_revenue,
        'today_sales':todays_sales_count,
        'todays_revenue':todays_revenue,
    }
    return render(request, 'IMS_admin/dashboard.html', context)

def edit_employee(request, id):
    try:
        employee = Employee.objects.get(id=id)
    except Employee.DoesNotExist:
        return redirect('employees')

    if request.method == 'POST':
        employee.First_name = request.POST['First_name']
        employee.last_name = request.POST['last_name']
        employee.date_of_birth = request.POST['date_of_birth']
        employee.email = request.POST['email']
        employee.address = request.POST['address']
        employee.phone_number = request.POST['phone_number']
        employee.designation = request.POST['designation']
        employee.date_of_joining = request.POST['date_of_joining']
        employee.gender = request.POST['gender']
        
        # Fetching the Department instance
        department_id = request.POST['department']
        try:
            employee.department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return redirect('edit_employee', id=id)
        
        if 'image' in request.FILES:
            employee.image = request.FILES['image']
        
        employee.save()
        return redirect('employees')
    else:
        departments = Department.objects.all()
        return render(request, 'IMS_Admin/edit_emp.html', {'employee': employee, 'departments': departments})
    
def edit_brand(request, id):
 if request.method == 'POST':
    brand=Brand.objects.get(id=id)

    brand.name = request.POST.get('name')
    brand.save()

    return redirect('brands')
 else:
     try:
            brand = Brand.objects.get(id=id)
     except Brand.DoesNotExist:
            # Handle case where brand with given id doesn't exist
            return redirect('brands')
     return render(request, "IMS_admin/edit_brand.html", {'brand': brand})
 
def edit_category(request, id):
 if request.method == 'POST':
    category=Category.objects.get(id=id)

    category.name = request.POST.get('name')
    category.save()

    return redirect('category')
 else:
     try:
         category=Category.objects.get(id=id)
     except Category.DoesNotExist:
            # Handle case where brand with given id doesn't exist
        return redirect('category')
     return render(request, "IMS_admin/edit_category.html", {'category': category}) 
 
def edit_department(request, id):
 if request.method == 'POST':
    department=Department.objects.get(id=id)

    department.name = request.POST.get('name')
    department.save()

    return redirect('departments')
 else:
     try:
         department=Department.objects.get(id=id)
     except Department.DoesNotExist:
            # Handle case where brand with given id doesn't exist
        return redirect('departments')
     return render(request, "IMS_admin/edit_department.html", {'department': department}) 
 

def edit_department(request, id):
 if request.method == 'POST':
    department=Department.objects.get(id=id)

    department.name = request.POST.get('name')
    department.save()

    return redirect('departments')
 else:
     try:
         department=Department.objects.get(id=id)
     except Department.DoesNotExist:
            # Handle case where brand with given id doesn't exist
        return redirect('departments')
     return render(request, "IMS_admin/edit_department.html", {'department': department}) 
 

def edit_manufacture(request, id):
    try:
        manufacture = Supplier.objects.get(id=id)
    except Supplier.DoesNotExist:
        return redirect('suppliers')

    if request.method == 'POST':
        print(request.POST)
        manufacture.Company_Name = request.POST.get('Supplier_name')
        manufacture.email = request.POST.get('Supplier_email')
        manufacture.contact_number = request.POST.get('Supplier_contact')
        manufacture.gstin_number = request.POST.get('gstin_number')
        manufacture.pan_number = request.POST.get('pan_number')
        manufacture.address = request.POST.get('Supplier_address')
        manufacture.bank_account_number = request.POST.get('bank_account_number')
        manufacture.ifsc_code = request.POST.get('ifsc_code')
        manufacture.bank_name = request.POST.get('bank_name')
        manufacture.business_type = request.POST.get('business_type')
        manufacture.business_license_number = request.POST.get('business_license')


        manufacture.save()

        return redirect('suppliers')
    else:
        return render(request, "IMS_admin/edit_manufacture.html", {'manufacture': manufacture})

def edit_product(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        return redirect('products')
    
    if request.method == 'POST':
        product.product_id = request.POST.get('product_id')
        cate=request.POST.get('category_name') 
        print(cate)
        category=Category.objects.get(id=cate)
        product.category = category
        product.product_name = request.POST.get('product_name')
        product.sku = request.POST.get('sku')
        product.unit = request.POST.get('unit')
        product.weight = request.POST.get('weight')
        product.weight_unit = request.POST.get('weightUnit')
        product.length = request.POST.get('length')
        product.width = request.POST.get('width')
        product.height = request.POST.get('height')
        product.dimension_unit = request.POST.get('dimensionUnit')
        product.cost_price = request.POST.get('cost_price')
        product.selling_price = request.POST.get('selling_price')
        manu=request.POST.get('Supplier_name')
        manufac=Supplier.objects.get(id=manu)
        product.Supplier = manufac
        brand=request.POST.get('brand_name') 
        brands=Brand.objects.get(id=brand)
        product.brand = brands
        product.upc = request.POST.get('upc')
        product.ean = request.POST.get('ean')
        product.mpn = request.POST.get('mpn')
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        
        product.description = request.POST.get('description')
        product.save()
        
        return redirect('products')
    else:
        categories = Category.objects.all()
        brands = Brand.objects.all()
        Suppliers = Supplier.objects.all()
        return render(request, "IMS_admin/edit_product.html", {'product': product, 'categories': categories, 'brands': brands, 'Suppliers': Suppliers})    



def edit_customer(request, customer_id):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return redirect('customers')

    if request.method == 'POST':
        customer.first_name = request.POST[('first_name')]
        customer.last_name = request.POST[('last_name')]
        customer.pan_no = request.POST[('pan_no')]
        customer.aadhar_no = request.POST[('aadhar_no')]
        customer.email = request.POST[('email_id')]
        customer.mobile_no = request.POST[('mobile_no')]
        customer.address = request.POST[('address')]
        customer.city = request.POST[('city')]
        customer.state = request.POST[('state')]
        customer.pin_code = request.POST[('pin_code')]
        customer.customer_id = request.POST[('customer_id')]
        customer.gst_no = request.POST[('gst_no')]
        customer.username = request.POST[('username')]
        customer.password = request.POST[('password')]


        customer.save()

        return redirect('customers')
    else:
        return render(request, "IMS_admin/edit_customer.html", {'customer': customer})
    
def add_customer(request):
    if request.method == "POST":
        cust_fname=request.POST.get('first_name')
        cust_lname=request.POST.get('last_name')
        cust_email=request.POST.get('email_id')
        cust_mobile=request.POST.get('mobile_no')
        cust_uname=request.POST.get('username')
        cust_password=request.POST.get('password')
        cust_pan=request.POST.get('pan_no')
        cust_aadhar=request.POST.get('aadhar_no')
        cust_Curr_add=request.POST.get('current_address')
        cust_perm_add=request.POST.get('address')
        cust_city=request.POST.get('city')
        cust_state=request.POST.get('state')
        cust_pincode=request.POST.get('pin_code')
        cust_cust_id=request.POST.get('customer_id')
        cust_gstin=request.POST.get('gst_no')
        
        newCustomer = Customer(
            first_name = cust_fname,
            last_name = cust_lname,
            pan_no = cust_pan,
            aadhar_no = cust_aadhar,
            email = cust_email,
            mobile_no = cust_mobile,
            current_address = cust_Curr_add,
            address = cust_perm_add,
            city = cust_city,
            state = cust_state,
            pin_code = cust_pincode,
            customer_id = cust_cust_id,
            gst_no = cust_gstin,
            username = cust_uname,
            password = cust_password,
        )
        newCustomer.save()
        return redirect('customers')
    else:
        
        return render(request,'Extra/customer.html')





@transaction.atomic
def createOrder(request):
    if request.method == "POST":
        customer_id = request.POST.get('customer_id')
        warehouse_id = request.POST.get('warehouse_id')
        sales_employee_id = request.POST.get('sales_employee_id')
        order_date = request.POST.get('order_date')

        # Fetch customer, sales employee, and warehouse objects
        customer = Customer.objects.get(customer_id=customer_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)
        sales_employee = Employee.objects.get(id=sales_employee_id)

        # Create order instance
        new_order = Order.objects.create(
            customer=customer,
            warehouse=warehouse,
            sales_employee=sales_employee,
            order_date=order_date
        )

        # Process each product in the order
        for i, product_id in enumerate(request.POST.getlist('product[]')):
            product = Product.objects.get(product_id=product_id)
            quantity = int(request.POST.getlist('quantity[]')[i])
            
            # Check and update stock
            stock = Stock.objects.get(product=product, warehouse=warehouse)
            if stock.stock_number < quantity:
                messages.error(request, f"Not enough stock for {product.product_name}.")
                continue  # Skip creating OrderDetail for this product

            stock.stock_number -= quantity
            stock.save()

            # Create OrderDetail
            OrderDetail.objects.create(
                order=new_order,
                product=product,
                quantity=quantity,
                unit_price=float(request.POST.getlist('unit_price[]')[i]),
                discount=float(request.POST.getlist('discount[]')[i]),
                tax_type=request.POST.getlist('tax_type[]')[i],
                tax_rate=float(request.POST.getlist('tax_rate[]')[i])
            )

        return redirect('orders')
    else:
        products = Product.objects.all()
        customers = Customer.objects.all()
        employees = Employee.objects.all()
        warehouses = Warehouse.objects.all()  # Load all warehouses
        return render(request, 'Extra/create_orders.html', {
            'products': products,
            'customers': customers,
            'employees': employees,
            'warehouses': warehouses  # Add warehouses to context
        })
    

def edit_order(request, order_id):
    order = Order.objects.get(id=order_id)
    order_details = OrderDetail.objects.filter(order=order)
    product = Product.objects.all()

    if request.method == 'POST':
        # Update Order model
        order.customer = request.POST.get('customer')
        order.sales_employee = request.POST.get('sales_employee')
        order.order_date = request.POST.get('order_date')
        order.invoice_generated = 'invoice_generated' in request.POST
        order.save()

        # Update OrderDetail models
        for detail in order_details:
            detail_id = detail.id
            detail.product = request.POST.get(f'product_{detail_id}')
            detail.quantity = request.POST.get(f'quantity_{detail_id}')
            detail.description = request.POST.get(f'description_{detail_id}')
            detail.unit_price = request.POST.get(f'unit_price_{detail_id}')
            detail.discount = request.POST.get(f'discount_{detail_id}')
            detail.tax_type = request.POST.get(f'tax_type_{detail_id}')
            detail.tax_rate = request.POST.get(f'tax_rate_{detail_id}')
            detail.save()

        return redirect('order_detail', id=order.id)

    return render(request, 'IMS_Admin/edit_order.html', {
        'order': order,
        'order_details': order_details,
        'product': product,
    })

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        gst_no = request.POST.get('gst_no')
        pan_no = request.POST.get('pan_no')
        address = request.POST.get('address')
        pincode = request.POST.get('pincode')
        password = request.POST.get('password')
        re_password = request.POST.get('re_password')

        if password != re_password:
            messages.error(request, 'Passwords do not match')
        else:
            if Company_details.objects.filter(email=email).exists():
                messages.error(request, 'A company with this email already exists')
            elif Company_details.objects.filter(pan_no=pan_no).exists():
                messages.error(request, 'A company with this PAN number already exists')
            elif Company_details.objects.filter(gst_no=gst_no).exists():
                messages.error(request, 'A company with this GST number already exists')
            else:
                company = Company_details(
                    name=name,
                    email=email,
                    phone_number=phone_number,
                    gst_no=gst_no,
                    pan_no=pan_no,
                    address=address,
                    pincode=pincode,
                    password=make_password(password)  # Hash the password
                )
                try:
                    company.save()
                    messages.success (request, 'Company registered successfully')
                    return redirect('admin_login')  # Redirect to the login page
                except Exception as e:
                    messages.error (request, f'Error: {e}')

    return render(request, 'IMS_Admin/register.html')

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from xhtml2pdf import pisa # type: ignore
from django.template.loader import render_to_string
from io import BytesIO

def convert_to_indian_currency(number):
    number_words = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
                    "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens_words = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    if number == 0:
        return "Zero"

    def convert(number):
        if number < 20:
            return number_words[number]
        elif number < 100:
            return tens_words[number // 10] + ('' if number % 10 == 0 else ' ' + number_words[number % 10])
        elif number < 1000:
            return number_words[number // 100] + " Hundred" + ('' if number % 100 == 0 else ' ' + convert(number % 100))
        elif number < 100000:
            return convert(number // 1000) + " Thousand" + ('' if number % 1000 == 0 else ' ' + convert(number % 1000))
        elif number < 10000000:
            return convert(number // 100000) + " Lakh" + ('' if number % 100000 == 0 else ' ' + convert(number % 100000))
        elif number < 1000000000:
            return convert(number // 10000000) + " Crore" + ('' if number % 10000000 == 0 else ' ' + convert(number % 10000000))
        else:
            return "Number too large"

    # Call the convert function and capitalize the first letter
    return convert(int(number)).capitalize()


def generate_invoice_pdf(request, id):
    inv = get_object_or_404(Invoice, id=id)
    inv_details = Invoice_items.objects.filter(invoice_id=inv)
    cmp = Company_details.objects.get(id=1)
    ord = inv.order_id
    cust = inv.customer

    # Calculate total and total tax amount, converting each value to float
    total_amount = sum(float(item.net_amount or 0) for item in inv_details)
    total_tax_amount = sum(float(item.tax_amount or 0) for item in inv_details)

    # Convert total amount to words using the custom function
    total_in_words = convert_to_indian_currency(total_amount) + " only."

    context = {
        'invoice': inv,
        'invoice_details': inv_details,
        'cmp_details': cmp,
        'customer': cust,
        'ord': ord,
        'total_amount': total_amount,
        'total_tax_amount': total_tax_amount,
        'total_in_words': total_in_words,
    }

    rendered_html = render_to_string('IMS_Admin/invoice_pdf.html', context)
    result = BytesIO()

    pdf = pisa.CreatePDF(BytesIO(rendered_html.encode("UTF-8")), dest=result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{id}.pdf"'
        return response
    else:
        return HttpResponse('We had some errors with the PDF generation', status=500)

    

def create_purchase_order(request):

    if request.method == 'POST':

        try:
            with transaction.atomic():
                supplier_id = request.POST.get('supplier_id')
                warehouse_id = request.POST.get('warehouse_id')
                expected_delivery_date = request.POST.get('expected_delivery_date')
                status = request.POST.get('status')
                total_amount = request.POST.get('total_amount')

                supplier = Supplier.objects.get(id=supplier_id)
                warehouse = Warehouse.objects.get(id=warehouse_id)
                
                # Create the Purchase Order
                purchase_order = PurchaseOrder.objects.create(
                    supplier=supplier,
                    warehouse=warehouse,
                    expected_delivery_date=expected_delivery_date,
                    status=status,
                    total_amount=total_amount,
                )
                
                # Loop through the products
                products = request.POST.getlist('product[]')
                quantities = request.POST.getlist('quantity[]')
                unit_prices = request.POST.getlist('unit_price[]')
                total_prices = request.POST.getlist('total_price[]')
                
                for i in range(len(products)):
                    product_id = products[i]
                    quantity = quantities[i]
                    unit_price = unit_prices[i]
                    total_price = total_prices[i]

                    product = Product.objects.get(product_id=product_id)
                    
                    # Create PurchaseOrderItem for each product
                    PurchaseOrderItem.objects.create(
                        purchase_order=purchase_order,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                    )
                
                messages.success(request, "Purchase Order has been placed successfully.")
                return redirect('purchase_orders')
        
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(reverse('purchase_order'))
    else:
        supplier=Supplier.objects.all()
        products=Product.objects.all()
        warehouses = Warehouse.objects.all()
        context={'supplier': supplier,
                'products': products,
            'warehouses': warehouses}

        return render(request, 'IMS_admin/purchase_form.html', context)

def manage_purchase_orders(request):
    purchase=PurchaseOrder.objects.all()
    context={'purchase': purchase}
    return render(request, 'IMS_admin/purchasetable.html', context)

def purchase_order_detail(request, order_id): 
    order = get_object_or_404(PurchaseOrder, pk=order_id)
    order_items = PurchaseOrderItem.objects.filter(purchase_order=order)

    context = {
        'order': order,
        'order_details': order_items,
    }
    if request.method == 'GET':
        return render(request, 'po_orderdetails.html', context)


def add_warehouse(request):    
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        capacity = int(request.POST.get('capacity'))
        current_stock = int(request.POST.get('current_stock'))
        manager_name = request.POST.get('manager_name')
        contact_number = request.POST.get('contact_number')
        notes = request.POST.get('notes', '')
        manager_instance = Employee.objects.get(pk=manager_name)

        warehouse = Warehouse(
            name=name,
            location=location,
            capacity=capacity,
            current_stock=current_stock,
            manager_name=manager_instance,
            manager_contact=manager_instance,
            email=manager_instance,
            contact_number=contact_number,
            notes=notes,
        )
        warehouse.save()
        
        return redirect('warehouses') # Adjust to your success page
    employees = Employee.objects.all()
    return render(request, 'IMS_admin/warehouse_form.html', {'employees': employees})



def get_manager_details(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        manager_id = request.GET.get('manager_id')
        manager = get_object_or_404(Employee, id=manager_id)
        data = {
            'email': manager.email,
            'contact_number': manager.phone_number
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Invalid request'}, status=400)
    

def warehouses(request):
    warehouses = Warehouse.objects.all()
    return render(request, 'IMS_admin/warehouse_table.html', {'warehouses':warehouses})

def edit_warehouse(request, id):
    warehouse = get_object_or_404(Warehouse, pk=id)
    if request.method == 'POST':
        warehouse.name = request.POST.get('name')
        warehouse.location = request.POST.get('location')
        warehouse.capacity = request.POST.get('capacity')
        warehouse.current_stock = request.POST.get('current_stock')
        warehouse.manager_name = Employee.objects.get(pk=request.POST.get('manager_name'))
        warehouse.manager_contact = request.POST.get('manager_contact')
        warehouse.email = request.POST.get('email')
        warehouse.contact_number = request.POST.get('contact_number')
        warehouse.notes = request.POST.get('notes', '')

        warehouse.save()
        return redirect('warehouses')  # Redirect to the warehouse list or detail view
    
    employees = Employee.objects.all()
    return render(request, 'IMS_admin/edit_warehouse.html', {'warehouse': warehouse, 'employees': employees})

def delete_warehouse(request, id):
    warehouse = get_object_or_404(Warehouse, pk=id)
    if request.method == 'POST':
        warehouse.delete()
        return redirect('warehouses')  

def low_stock_alerts(request):
    low_stock_items = Stock.objects.filter(stock_number__lt=models.F('low_stock_threshold'))

    context = {
        'low_stock_items': low_stock_items,
    }
    return render(request, 'IMS_Admin/low_stock_items.html', context)

import logging

logger = logging.getLogger(__name__)


@transaction.atomic
def accounts_receivable(request):
    if request.method == 'POST':
        invoice_id = request.POST.get('invoice')
        new_payment = Decimal(request.POST.get('amount_paid', '0.0'))
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes')
        status = request.POST.get('status')
        balance_due = Decimal(request.POST.get('balance_due', '0.0'))
        payment_date = request.POST.get('payment_date') if request.POST.get('payment_date') else timezone.now().date()

        print("POST data:", request.POST)
        try:
            invoice_obj = Invoice.objects.get(id=invoice_id)
            ar, created = AccountsReceivable.objects.get_or_create(
                invoice=invoice_obj,
                defaults={
                    'customer': invoice_obj.customer,
                    'total_amount': invoice_obj.total_amount,
                    'balance_due': balance_due,
                    'due_date': invoice_obj.due_date,
                    'amount_paid': new_payment,
                    'payment_date': payment_date,
                    'payment_method': payment_method,
                    'notes': notes,
                    'status': status,
                }
            )

            if not created:
                ar.amount_paid += new_payment
                ar.balance_due = balance_due
                ar.payment_date = payment_date
                ar.payment_method = payment_method
                ar.notes = notes
                ar.status = status
                ar.save()

            messages.success(request, 'Accounts Receivable updated successfully.')
            return redirect('manage_accounts_receviable')
        except Invoice.DoesNotExist:
            messages.error(request, 'Invalid Invoice ID.')
            return redirect('accounts_receivable')
        except Exception as e:
            logger.exception("Error processing accounts receivable:")
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('accounts_receivable')
    else:
        invoices = Invoice.objects.all()
        context = {'invoices': invoices}
        return render(request, 'IMS_admin/accounts_receivable.html', context)



def manage_accounts_payable(request):
    accounts=AccountsPayable.objects.all()
    context={
        'accounts':accounts
    }
    return render(request, 'IMS_admin/accounts_payable_table.html', context)

def purchase_order_detail(request):
    return HttpResponse("Accounts Payable page")

def edit_purchase_order(request, purchase_order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
    warehouses = Warehouse.objects.all()
    suppliers = Supplier.objects.all()
    products = Product.objects.all()

    if request.method == 'POST':
        purchase_order.warehouse_id = request.POST.get('warehouse_id')
        purchase_order.supplier_id = request.POST.get('supplier_id')

        try:
            # Ensure valid date format
            order_date_str = request.POST.get('order_date')
            expected_delivery_date_str = request.POST.get('expected_delivery_date')

            purchase_order.order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date()
            purchase_order.expected_delivery_date = datetime.strptime(expected_delivery_date_str, '%Y-%m-%d').date()
            
            purchase_order.status = request.POST.get('status')

            # Save the purchase order
            purchase_order.save()
            return redirect('purchase_orders')  # Replace with the actual name of the purchase orders list view

        except ValueError as e:
            messages.error(request, f"Invalid date format: {str(e)}")
            return redirect(reverse('edit_purchase_order', args=[purchase_order_id]))

    context = {
        'purchase_order': purchase_order,
        'warehouses': warehouses,
        'suppliers': suppliers,
        'products': products,
    }
    return render(request, 'IMS_admin/edit_purchseform.html', context)



def delete_purchase_orders(request, id):
    if request.method == "POST":
        purchase_orders = get_object_or_404(PurchaseOrder, id=id)
        purchase_orders.delete()
        return redirect('purchase_orders')

def manage_accounts_receviable(request):
    accounts=AccountsReceivable.objects.all()
    context={
        'accounts':accounts
    }
    return render(request, 'IMS_admin/accounts_receviable_table.html', context)

def accounts_payable(request):
    purchase_orders=PurchaseOrder.objects.all()


def accounts_payable(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        purchase_order_id = request.POST.get('purchase_order')
        total_payable_amount = request.POST.get('total_payable_amount')
        balance_due = request.POST.get('balance_due')
        amount_paid = request.POST.get('amount_paid')
        due_date = request.POST.get('due_date')
        payment_date = request.POST.get('payment_date')
        status = request.POST.get('status')

        # Fetch the related supplier and purchase order objects
        supplier = Supplier.objects.get(name=supplier_id)
        purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)

        # Create a new AccountsPayable record
        accounts_payable = AccountsPayable(
            supplier=supplier,
            purchase_order=purchase_order,
            total_payable_amount=total_payable_amount,  
            amount_paid=amount_paid,
            balance_due=balance_due,
            due_date=due_date,
            payment_date=payment_date,
            status=status
        )
        accounts_payable.save()

        # Redirect to a success page or the same form with a success message
        return redirect('manage_accounts_payable')  # Replace 'success_url' with your success page URL name

    # Handle GET request
    purchase_orders = PurchaseOrder.objects.all()
    suppliers = Supplier.objects.all()

    context = {
        'purchase_orders': purchase_orders,
        'suppliers': suppliers
    }

    return render(request, 'IMS_admin/accounts_payable.html', context)


def stock_transfer_request(request):
    if request.method == 'POST':
        source_warehouse_id = request.POST.get('source_warehouse')
        destination_warehouse_id = request.POST.get('destination_warehouse')
        product_id = request.POST.get('product_name')
        quantity = request.POST.get('quantity')

        source_warehouse = Warehouse.objects.get(id=source_warehouse_id)
        destination_warehouse = Warehouse.objects.get(id=destination_warehouse_id)

        product_instance = Product.objects.get(product_id=product_id)  # Fetch by product_id

        transfer_request = StockTransferRequest(
            source_warehouse=source_warehouse,
            destination_warehouse=destination_warehouse,
            product=product_instance,
            quantity=quantity
        )
        transfer_request.save()

        return redirect(reverse('stock_transfer_request_table'))

    warehouses = Warehouse.objects.all()
    products = Product.objects.all()

    return render(request, 'IMS_admin/stock_transfer_request.html', {
        'warehouses': warehouses,
        'products': products
    })

def stock_transfer_request_table(request):

    requests=StockTransferRequest.objects.all()
    return render(request, 'IMS_admin/stock_transfer_request_table.html', {
        'requests': requests,
    })


def edit_stock_transfer_request(request, request_id):
    stock_transfer_request = get_object_or_404(StockTransferRequest, id=request_id)

    if request.method == 'POST':
        stock_transfer_request.source_warehouse_id = request.POST.get('source_warehouse')
        stock_transfer_request.destination_warehouse_id = request.POST.get('destination_warehouse')
        stock_transfer_request.product_id = request.POST.get('product_name')
        stock_transfer_request.quantity = request.POST.get('quantity')
        stock_transfer_request.request_date = request.POST.get('request_date')
        
        stock_transfer_request.save()

        return redirect(reverse('stock_transfer_request_table'))

    warehouses = Warehouse.objects.all()
    products = Product.objects.all()

    return render(request, 'IMS_admin/edit_stock_transfer_request.html', {
        'request': stock_transfer_request,
        'warehouses': warehouses,
        'products': products
    })

def delete_stock_transfer_request(request, request_id):
    transfer_request = get_object_or_404(StockTransferRequest, id=request_id)
    if request.method == 'POST':
        transfer_request.delete()
        return redirect('stock_transfer_request_table')

def stock_transfer_send(request):
    transfer_requests = StockTransferRequest.objects.all()

    if request.method == 'POST':
        transfer_request_id = request.POST.get('transfer_request_id')
        quantity_sent = request.POST.get('quantity_sent')

        if not transfer_request_id or not quantity_sent:
            raise ValueError("Transfer request and quantity sent are required.")
        
        transfer_request = StockTransferRequest.objects.get(id=transfer_request_id)
        quantity_sent = int(quantity_sent)
        
        if quantity_sent <= 0:
            raise ValueError("Quantity sent must be a positive integer.")
        
        # Fetch Stock records
        source_stock = Stock.objects.get(warehouse=transfer_request.source_warehouse, product=transfer_request.product)
        destination_stock = Stock.objects.get_or_create(warehouse=transfer_request.destination_warehouse, product=transfer_request.product, brand=source_stock.brand, supplier=source_stock.supplier,defaults={'stock_number': 0})[0]
        
        if quantity_sent > source_stock.stock_number:
            raise ValueError("Not enough stock in the source warehouse.")
        
        # Update stock numbers
        source_stock.stock_number -= quantity_sent
        
        
        # Save updated stock records
        source_stock.save()
        destination_stock.save()

        # Save the transfer record
        stock_transfer_send = StockTransferSend(
            transfer_request=transfer_request,
            source_warehouse=transfer_request.source_warehouse,
            destination_warehouse=transfer_request.destination_warehouse,
            product=transfer_request.product,
            quantity_requested=transfer_request.quantity,
            quantity_sent=quantity_sent
        )
        stock_transfer_send.save()

        return redirect(reverse('stock_transfer_send_table'))
    

        return render(request, 'IMS_admin/stock_transfer_send.html', {
            'error': str(e),
            'transfer_requests': transfer_requests
        })

    return render(request, 'IMS_admin/stock_transfer_send.html', {
        'transfer_requests': transfer_requests
    })

def stock_transfer_send_table(request):

    transfers=StockTransferSend.objects.all()
    return render(request, 'IMS_admin/stock_transfer_send_table.html', {
        'transfers': transfers,
    })

def edit_stock_transfer_send(request, id):
    stock_transfer_send = get_object_or_404(StockTransferSend, pk=id)
    transfer_requests = StockTransferRequest.objects.all()

    if request.method == 'POST':
        quantity_sent = int(request.POST.get('quantity_sent'))
        original_quantity_sent = stock_transfer_send.quantity_sent

        try:
            if quantity_sent <= 0:
                raise ValueError("Quantity sent must be a positive integer.")
            
            # Fetch Stock records for source and destination
            source_stock = Stock.objects.get(warehouse=stock_transfer_send.source_warehouse, product=stock_transfer_send.product)
            destination_stock = Stock.objects.get(warehouse=stock_transfer_send.destination_warehouse, product=stock_transfer_send.product)

            # Revert the original stock transfer
            source_stock.stock_number += original_quantity_sent
            destination_stock.stock_number -= original_quantity_sent

            # Check for new transfer feasibility
            if quantity_sent > source_stock.stock_number:
                raise ValueError("Not enough stock in the source warehouse after reverting the original transfer.")

            # Apply the new stock transfer
            source_stock.stock_number -= quantity_sent
            destination_stock.stock_number += quantity_sent

            # Validate that the current stock does not fall below zero
            if source_stock.stock_number < 0 or destination_stock.stock_number < 0:
                raise ValidationError("Current stock cannot be negative.")

            # Save updated stock records
            source_stock.save()
            destination_stock.save()

            # Update the stock transfer record
            stock_transfer_send.quantity_sent = quantity_sent
            stock_transfer_send.save()

            return redirect(reverse('stock_transfer_send_table'))
        
        except (ValueError, ValidationError) as e:
            return render(request, 'IMS_admin/edit_stock_transfer_send.html', {
                'error': str(e),
                'stock_transfer_send': stock_transfer_send,
                'transfer_requests': transfer_requests,
            })

    return render(request, 'IMS_admin/edit_stock_transfer_send.html', {
        'stock_transfer_send': stock_transfer_send,
        'transfer_requests': transfer_requests,
    })

def delete_stock_transfer_send(request, id):
    stock_transfer_send = get_object_or_404(StockTransferSend, pk=id)
    source_warehouse = stock_transfer_send.source_warehouse
    quantity_to_restore = stock_transfer_send.quantity_sent

    if request.method == 'POST':
        with transaction.atomic():
            # Restore the stock in the source warehouse
            source_warehouse.current_stock += quantity_to_restore
            source_warehouse.save()

            # Delete the stock_transfer_send entry
            stock_transfer_send.delete()

        return redirect('stock_transfer_send_table')

from django.db import IntegrityError
def stock_transfer_received(request):
    if request.method == 'POST':
        transfer_request_id = request.POST.get('transfer_request_id')
        quantity_received = int(request.POST.get('quantity_received', 0))
        damaged_stock = int(request.POST.get('damaged_stock', 0))
        discrepancy_notes = request.POST.get('discrepancy_notes', '')

        try:
            # Fetch the transfer request
            transfer_request = get_object_or_404(StockTransferSend, id=transfer_request_id)
            destination_warehouse = transfer_request.destination_warehouse

            # Create the StockTransferReceive instance
            transfer_receive = StockTransferReceive(
                transfer_request=transfer_request,
                destination_warehouse=destination_warehouse,
                product=transfer_request.product,
                quantity_send=transfer_request.quantity_sent,  # Received directly
                damaged_stock=damaged_stock,
                quantity_received=quantity_received,
                discrepancy_notes=discrepancy_notes
            )
            transfer_receive.save()

            # Update the stock in the destination warehouse
            # Fetch or create the stock instance for the destination warehouse and product
            destination_warehouse_stock, created = Stock.objects.get_or_create(
                warehouse=destination_warehouse,
                product=transfer_request.product,
                defaults={'stock_number': 0}  # Initialize with zero if not found
            )

            # Update the stock quantity, accounting for damaged goods
            destination_warehouse_stock.stock_number += (quantity_received - damaged_stock)
            destination_warehouse_stock.save()

            return redirect('stock_transfer_received_table')  # Redirect to a success page or another view

        except IntegrityError as e:
            # Handle integrity errors, e.g., if stock is not found
            return render(request, 'IMS_admin/stock_transfer_received.html', {'error': str(e)})

    else:
        transfer_request_id = None

    # Preload the StockTransferSend objects for the dropdown
    transfer_requests = StockTransferSend.objects.all()

    context = {
        'transfer_requests': transfer_requests,
    }
    return render(request, 'IMS_admin/stock_transfer_received.html', context)


def stock_transfer_received_table(request):

    receives=StockTransferReceive.objects.all()
    return render(request, 'IMS_admin/stock_transfer_received_table.html', {
        'receives': receives,
    })

def edit_stock_transfer_received(request, pk):
    transfer_receive = get_object_or_404(StockTransferReceive, pk=pk)
    
    if request.method == 'POST':
        transfer_receive.quantity_received = int(request.POST.get('quantity_received', 0))
        transfer_receive.damaged_stock = int(request.POST.get('damaged_stock', 0))
        transfer_receive.discrepancy_notes = request.POST.get('discrepancy_notes', '')
        
        try:
            transfer_receive.save()

            destination_warehouse = transfer_receive.destination_warehouse
            destination_warehouse.current_stock += (transfer_receive.quantity_received - transfer_receive.damaged_stock)
            destination_warehouse.save()

            return redirect('stock_transfer_received_table')
        except IntegrityError as e:
            return render(request, 'IMS_admin/edit_stock_transfer_received.html', {'error': str(e), 'transfer_receive': transfer_receive})

    context = {
        'transfer_receive': transfer_receive,
    }
    return render(request, 'IMS_admin/edit_stock_transfer_received.html', context)

def delete_stock_transfer_received(request, pk):
    transfer_receive = get_object_or_404(StockTransferReceive, pk=pk)
    destination_warehouse = transfer_receive.destination_warehouse
    quantity_to_remove = transfer_receive.quantity_received - transfer_receive.damaged_stock

    if request.method == 'POST':
        with transaction.atomic():
            # Update the stock in the destination warehouse
            destination_warehouse.current_stock -= quantity_to_remove

            # Ensure stock doesn't go negative
            if destination_warehouse.current_stock < 0:
                messages.error(request, "Cannot delete, insufficient stock.")
                return redirect('stock_transfer_received_table')

            destination_warehouse.save()

            # Delete the transfer_receive entry
            transfer_receive.delete()

        return redirect('stock_transfer_received_table')


def edit_purchase_order(request, purchase_order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
    warehouses = Warehouse.objects.all()
    suppliers = Supplier.objects.all()
    products = Product.objects.all()

    if request.method == 'POST':
        purchase_order.warehouse_id = request.POST.get('warehouse_id')
        purchase_order.supplier_id = request.POST.get('supplier_id')

        try:
            # Ensure valid date format
            order_date_str = request.POST.get('order_date')
            expected_delivery_date_str = request.POST.get('expected_delivery_date')

            purchase_order.order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date()
            purchase_order.expected_delivery_date = datetime.strptime(expected_delivery_date_str, '%Y-%m-%d').date()
            
            purchase_order.status = request.POST.get('status')

            # Save the purchase order
            purchase_order.save()
            return redirect('purchase_orders')  # Replace with the actual name of the purchase orders list view

        except ValueError as e:
            messages.error(request, f"Invalid date format: {str(e)}")
            return redirect(reverse('edit_purchase_order', args=[purchase_order_id]))

    context = {
        'purchase_order': purchase_order,
        'warehouses': warehouses,
        'suppliers': suppliers,
        'products': products,
    }
    return render(request, 'IMS_admin/edit_purchseform.html', context)


def edit_accounts_payable(request, id):
    accounts_payable = get_object_or_404(AccountsPayable, id=id)

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        purchase_order_id = request.POST.get('purchase_order')
        total_payable_amount = request.POST.get('total_payable_amount')
        balance_due = request.POST.get('balance_due')
        amount_paid = request.POST.get('amount_paid')
        due_date = request.POST.get('due_date')
        payment_date = request.POST.get('payment_date')
        status = request.POST.get('status')

        # Fetch the related supplier and purchase order objects
        supplier = Supplier.objects.get(name=supplier_id)
        purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)

        # Update the AccountsPayable record
        accounts_payable.supplier = supplier
        accounts_payable.purchase_order = purchase_order
        accounts_payable.total_payable_amount = total_payable_amount
        accounts_payable.balance_due = balance_due
        accounts_payable.amount_paid = amount_paid
        accounts_payable.due_date = due_date
        accounts_payable.payment_date = payment_date
        accounts_payable.status = status

        accounts_payable.save()

        return redirect('manage_accounts_payable')

    # Handle GET request
    purchase_orders = PurchaseOrder.objects.all()
    suppliers = Supplier.objects.all()

    context = {
        'accounts_payable': accounts_payable,
        'purchase_orders': purchase_orders,
        'suppliers': suppliers
    }

    return render(request, 'IMS_admin/edit_accounts_payable.html', context)


def delete_accounts_payable(request, id):
    if request.method=="POST":
        Account_payable=AccountsPayable.objects.get(id=id)
        Account_payable.delete()
        return redirect('manage_accounts_payable')
    
def edit_accounts_receviable(request, id):
    ar = get_object_or_404(AccountsReceivable, id=id)
    
    if request.method == 'POST':
        invoice_id = request.POST.get('invoice')
        new_payment = float(request.POST.get('amount_paid', '0.0'))
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes')
        status = request.POST.get('status')
        balance_due = float(request.POST.get('balance_due', '0.0'))
        payment_date = request.POST.get('payment_date') if request.POST.get('payment_date') else timezone.now().date()

        try:
            invoice_obj = Invoice.objects.get(id=invoice_id)

            ar.invoice = invoice_obj
            ar.customer = invoice_obj.customer
            ar.total_amount = invoice_obj.total_amount
            ar.amount_paid = new_payment
            ar.balance_due = balance_due
            ar.due_date = invoice_obj.due_date
            ar.payment_date = payment_date
            ar.payment_method = payment_method
            ar.notes = notes
            ar.status = status
            ar.save()

            messages.success(request, 'Accounts Receivable updated successfully.')
            return redirect('manage_accounts_receviable')
        except Invoice.DoesNotExist:
            messages.error(request, 'Invalid Invoice ID.')
            return redirect('edit_accounts_receviable', id=id)
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect('edit_accounts_receviable', id=id)

    invoices = Invoice.objects.all()
    context = {
        'ar': ar,
        'invoices': invoices,
    }
    return render(request, 'IMS_admin/edit_accounts_receivable.html', context)


def delete_manage_accounts(request, id):
    if request.method=="POST":
        manage_accounts=AccountsReceivable.objects.get(id=id)
        manage_accounts.delete()
        return redirect('manage_accounts_receviable')


def edit_stock_update(request, id):
    stock_instance = get_object_or_404(Stock, id=id)
    
    if request.method == "POST":
        warehouse_id = request.POST.get('warehouse_id')
        supplier_id = request.POST.get('supplier_id')
        brand_id = request.POST.get('brand_id')
        product_id = request.POST.get('product_name')
        stock_status_str = request.POST.get('stock_status')
        stock_status = stock_status_str == 'In Stock'
        stock_num = int(request.POST.get('stock_num'))
        min_stock = int(request.POST.get('min_stock'))

        stock_instance.warehouse = Warehouse.objects.get(pk=warehouse_id)
        stock_instance.supplier = Supplier.objects.get(pk=supplier_id)
        stock_instance.brand = Brand.objects.get(pk=brand_id)
        stock_instance.product = Product.objects.get(product_id=product_id)
        stock_instance.stock_status = stock_status
        stock_instance.stock_number = stock_num
        stock_instance.low_stock_threshold = min_stock

        stock_instance.save()
        messages.success(request, "Stock updated successfully.")
        return redirect('stock')

    warehouses = Warehouse.objects.all()
    suppliers = Supplier.objects.all()
    brands = Brand.objects.all()
    products = Product.objects.all()

    context = {
        'stock_instance': stock_instance,
        'warehouses': warehouses,
        'suppliers': suppliers,
        'brands': brands,
        'products': products
    }
    return render(request, 'IMS_Admin/edit_stock_update.html', context)    

def delete_stock_update(request, id):
    stock = get_object_or_404(Stock, id=id)
    stock.delete()
    messages.success(request, "Stock entry deleted successfully.")
    return redirect('stock')


def edit_restock(request, restock_id):
    restock = get_object_or_404(Restock, id=restock_id)
    
    if request.method == "POST":
        warehouse_id = request.POST.get('warehouse_id')
        employee_id = request.POST.get('employee_id')
        product_id = request.POST.get('product_id')
        purchase_order_id = request.POST.get('purchase_order')
        quantity_added = request.POST.get('quantity_added')

        if not quantity_added.isdigit():
            messages.error(request, "Invalid quantity. Please enter a numeric value.")
            return redirect('edit_restock', restock_id=restock_id)

        quantity_added = int(quantity_added)
        
        try:
            warehouse = Warehouse.objects.get(pk=warehouse_id)
            employee = Employee.objects.get(pk=employee_id)
            product = Product.objects.get(pk=product_id)
            purchase_order = PurchaseOrder.objects.get(pk=purchase_order_id)

            # Adjust stock
            stock = Stock.objects.get(warehouse=warehouse, product=product)
            stock.stock_number -= restock.quantity_added  # Remove old quantity
            stock.stock_number += quantity_added  # Add new quantity
            stock.save()

            restock.warehouse = warehouse
            restock.product = product
            restock.purchase_order = purchase_order
            restock.quantity_added = quantity_added
            restock.restocked_by = employee
            restock.save()

            return redirect('restock_table')
        except:
            return HttpResponse("Error")

    context = {
        'restock': restock,
        'employees': Employee.objects.all(),
        'products': Product.objects.all(),
        'warehouses': Warehouse.objects.all(),
        'purchase_orders': PurchaseOrder.objects.all(),
    }
    return render(request, 'IMS_Admin/edit_restock.html', context)

def delete_restock(request, restock_id):
    restock = get_object_or_404(Restock, id=restock_id)
    
    if request.method == "POST":
        # Adjust stock before deletion
        stock = Stock.objects.get(warehouse=restock.warehouse, product=restock.product)
        stock.stock_number -= restock.quantity_added
        stock.save()
        
        restock.delete()
        return redirect('restock_table')