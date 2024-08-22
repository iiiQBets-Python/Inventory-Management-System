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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer



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
                request.session['userid']=employee.id
                return redirect('dashboard')
                # return render(request, 'base/base.html', {'emp': employee})
            else:
                messages.error(request, 'Invalid password')
                return redirect('admin_login')
        
        except Employee.DoesNotExist:
            try:
                # Check if the user is a Company
                company = Company_details.objects.get(email=username)
                if check_password(password, company.password):
                    return render(request, 'base/base.html', {'company': company})
                else:
                    messages.error(request, 'Invalid password')
                    return redirect('admin_login')
            except Company_details.DoesNotExist:
                messages.error(request, 'Invalid username')
                return redirect('admin_login')
    
    return render(request, 'IMS_Admin/login.html')


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
            'unit_price': float(detail.product.selling_price)
            
        } for detail in OrderDetail.objects.filter(order=order)]
    } for order in ord]
    
    context = {
        'customer': json.dumps(customer_data),
        'order': json.dumps(order_data),
        'company': company
    }
    return render(request, 'IMS_admin/invoice11.html', context)

def log_out(request):
    print("logout successful")
    logout(request)
    return redirect('home')




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
        upc = request.POST.get('upc')
        ean = request.POST.get('ean')
        mpn = request.POST.get('mpn')
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
            upc=upc,
            ean=ean,
            mpn=mpn,
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
        supplier_id = request.POST.get('supplier_id')
        upc = request.POST.get('upc')
        brand_id = request.POST.get('brand_id')
        mpn = request.POST.get('mpn')
        product_id = request.POST.get('product_name')  # Correcting to get product_id
        stock_status_str = request.POST.get('stock_status')
        stock_status = stock_status_str == 'In Stock'
        stock_num = int(request.POST.get('stock_num'))
        ean = request.POST.get('ean')

        supplier_instance = Supplier.objects.get(pk=supplier_id)
        brand_instance = Brand.objects.get(pk=brand_id)

        try:
            product_instance = Product.objects.get(product_id=product_id)  # Fetch by product_id
        except Product.DoesNotExist:
            # Handle the error if the product doesn't exist
            messages.error(request, "Product does not exist.")
            return redirect('stockupdate')

        try:
            existing_stock = stock.objects.get(
                supplier=supplier_instance,
                upc=upc,
                brand=brand_instance,
                mpn=mpn,
                product_name=product_instance,
                ean=ean
            )
            existing_stock.stock_number += stock_num
            existing_stock.stock_status = stock_status
            existing_stock.save()
        except stock.DoesNotExist:
            new_stock = stock(
                supplier=supplier_instance,
                upc=upc,
                brand=brand_instance,
                mpn=mpn,
                ean=ean,
                stock_status=stock_status,
                stock_number=stock_num,
                product_name=product_instance,
            )
            new_stock.save()

        return redirect('stock')
    else:
        suppliers = Supplier.objects.all()
        products = Product.objects.all()
        brands = Brand.objects.all()
        context = {
            'suppliers': suppliers,
            'products': products,
            'brands': brands
        }
        return render(request, 'IMS_Admin/stockupdate.html', context)



def stock_table(request):
    stocks=stock.objects.all()
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
        return redirect('supplier')

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
            product = stock.objects.get(product_name=order_detail.product.product_name)
            product.stock_number -= order_detail.quantity
            product.save()
        except stock.DoesNotExist:
            return HttpResponse("Product not found in stock.")

        return HttpResponse("Order created successfully and stock stock updated.")
    else:
        return HttpResponse("Invalid request method. Must be POST.")


def invoice_table(request):
    inv=invoice.objects.all()
    context={
        'invoices':inv
    }
    return render(request, 'IMS_Admin/invoicetable.html', context)

def delete_invoice(request, id):
    inv=invoice.objects.select_related('customer').all()
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
        customer_id = request.POST.get('customer_name')
        invoice_date = request.POST.get('invoice_date')
        due_date = request.POST.get('due_date')
        total_amount = float(request.POST.get('total', 0))

        new_invoice = invoice.objects.create(
            order_id=Order.objects.get(id=order_id),
            customer=Customer.objects.get(first_name=customer_id),
            invoice_date=invoice_date,
            due_date=due_date,
            total_amount=total_amount
        )
        ord=Order.objects.get(id=order_id)
        ord.invoice_generated=True
        ord.save()

        items_json = request.POST.get('items')
        items = json.loads(items_json)

        for item in items:
            product = Product.objects.get(product_name=item['product'])
            item['subtotal']=Decimal(item['subtotal'])
            item['unit_price']=Decimal(item['unit_price'])
            invoice_items.objects.create(
                invoice_id=new_invoice,
                product_name=product,
                selling_price=item['unit_price'],
                net_amount=item['subtotal'],
                quantity=int(item['quantity']),
                description=item['item_description'],
                tax_type=item['tax_type'],
                tax_rate=item['tax_rate'],
                tax_amount=item['tax_amount'],
                discount=item['discount']

            )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
        'notifications',
        {
            'type': 'notification_message',
            'message': f'New invoice created for order {order_id}!'
        }
        )
        
        return redirect('invoices')  # Change this to your success URL



def view_invoice(request, id):
    inv = get_object_or_404(invoice, id=id)
    inv_details = invoice_items.objects.filter(invoice_id=inv)
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
    inv_count=invoice.objects.all()
    invoice_count=inv_count.count()
    total_revenue=0
    for i in inv_count:
        total_revenue+=i.total_amount
    today = timezone.now().date()
    
    # Get today's invoices
    todays_invoices = invoice.objects.filter(invoice_date=today)
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
        return redirect('supplier')

    if request.method == 'POST':
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

        return redirect('supplier')
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





def createOrder(request):
    
    if request.method == "POST":
        customer_id = request.POST.get('customer_id')
        customer_name = request.POST.get('customer_id')
        sales_employee_id = request.POST.get('sales_employee_id')
        sales_employee_name = request.POST.get('sales_employee')
        order_date = request.POST.get('order_date')
        products = request.POST.getlist('product[]')
        descriptions = request.POST.getlist('item_description[]')
        quantities = request.POST.getlist('quantity[]')
        unit_prices = request.POST.getlist('unit_price[]')
        discounts = request.POST.getlist('discount[]')
        tax_types = request.POST.getlist('tax_type[]')
        tax_rates = request.POST.getlist('tax_rate[]')

        # Fetch customer object
        
        customer = Customer.objects.get(customer_id=customer_id)

        # Fetch sales employee object
        sales_employee = Employee.objects.get(pk=sales_employee_id)

        # Create order instance
        new_order = Order.objects.create(
            customer=customer,
            order_date=order_date,
            sales_employee=sales_employee
        )

        # Create order detail instances
        for i in range(len(products)):
            product = Product.objects.get(pk=products[i])
            OrderDetail.objects.create(
                order=new_order,
                product=product,
                description=descriptions[i],
                quantity=int(quantities[i]),
                unit_price=float(unit_prices[i]),
                discount=float(discounts[i]),
                tax_type=tax_types[i],
                tax_rate=float(tax_rates[i])
            )

        
        return redirect('orders')

    else:
        products = Product.objects.all()
        customers = Customer.objects.all()
        employees = Employee.objects.all()
        context = {
            'products': products,
            'customers': customers,
            'employees': employees,
        }
        return render(request, 'Extra/create_orders.html', context)
    

def edit_order(request, id):
    order = get_object_or_404(Order, id=id)
    order_details = OrderDetail.objects.filter(order=order)

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
    inv = get_object_or_404(invoice, id=id)
    inv_details = invoice_items.objects.filter(invoice_id=inv)
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




def edit_stock(request, id):
    try:
        stock = stock.objects.get(id=id)
    except stock.DoesNotExist:
        return redirect('stock')

    if request.method == 'POST':
        try:
            Supplier_instance = Supplier.objects.get(id=request.POST.get('Supplier_name'))
            brand_instance = Brand.objects.get(id=request.POST.get('brand_name'))
        except (Supplier.DoesNotExist, Brand.DoesNotExist):
            return redirect('stock')  # Or handle the error as you see fit

        stock.Supplier = Supplier_instance
        stock.upc = request.POST.get('upc')
        stock.brand = brand_instance
        stock.mpn = request.POST.get('mpn')
        stock.product_name = request.POST.get('product_name')
        stock_status_str = request.POST.get('stock_status')
        stock.stock_status = stock_status_str == 'In Stock'
        stock.stock_number = request.POST.get('stock_num')
        # stock.min_stock = request.POST.get('min_stock')
        stock.ean = request.POST.get('ean')
        stock.save()

        return redirect('stock')
    else:
        manu = Supplier.objects.all()
        prod = Product.objects.all()
        brand = Brand.objects.all()
        return render(request, "IMS_admin/edit_stock.html", {'stock': stock, 'prod': prod, 'brand': brand, 'manu': manu})
    

def delete_stock(request, id):
    if request.method=="POST":
        stock=stock.objects.get(id=id)
        stock.delete()
        return redirect('stock')
    

def create_purchase_order(request):

    if request.method == 'POST':

        try:
            with transaction.atomic():
                supplier_id = request.POST.get('supplier_id')
                expected_delivery_date = request.POST.get('expected_delivery_date')
                status = request.POST.get('status')
                total_amount = request.POST.get('total_amount')

                supplier = Supplier.objects.get(id=supplier_id)
                
                # Create the Purchase Order
                purchase_order = PurchaseOrder.objects.create(
                    supplier=supplier,
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
        context={'supplier': supplier,
                'products':products}

        return render(request, 'IMS_admin/purchase_form.html', context)

def manage_purchase_orders(request):
    purchase=PurchaseOrder.objects.all()
    context={'purchase': purchase}
    return render(request, 'IMS_admin/purchasetable.html', context)

def manage_warehouse_locations(request):
    return HttpResponse("Manage stock Locations page")

def manage_warehouse_stock(request):
    return HttpResponse("Manage stock Stock page")

def low_stock_alerts(request):
    return HttpResponse("Low Stock Alerts page")

def accounts_receivable(request):
    if request.method == 'POST':
        invoice_id = request.POST.get('invoice')
        new_payment = float(request.POST.get('amount_paid', '0.0'))
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes')
        status = request.POST.get('status')
        balance_due = float(request.POST.get('balance_due', '0.0'))  # Use the balance due from the form
        payment_date = request.POST.get('payment_date') if request.POST.get('payment_date') else timezone.now().date()

        try:
            invoice_obj = invoice.objects.get(id=invoice_id)
            ar, created = AccountsReceivable.objects.get_or_create(
                invoice=invoice_obj,
                defaults={
                    'customer': invoice_obj.customer,
                    'total_amount': invoice_obj.total_amount,
                    'balance_due': balance_due,  # Use the calculated balance due
                    'due_date': invoice_obj.due_date,
                    'amount_paid': new_payment,
                    'payment_date': payment_date,
                    'payment_method': payment_method,
                    'notes': notes,
                    'status': status,
                }
            )

            if not created:
                # Only update the fields if the AccountsReceivable object was not newly created
                ar.amount_paid += new_payment
                ar.balance_due = balance_due  # Use the balance due passed from the form
                ar.payment_date = payment_date
                ar.payment_method = payment_method
                ar.notes = notes
                ar.status = status
                ar.save()

            messages.success(request, 'Accounts Receivable updated successfully.')
            return redirect('manage_accounts_receivable')
        except invoice.DoesNotExist:
            messages.error(request, 'Invalid Invoice ID.')
            return redirect('accounts_receivable')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect('accounts_receivable')
    else:
        invoices = invoice.objects.all()
        context = {'invoices': invoices}
        return render(request, 'IMS_admin/accounts_receivable.html', context)

    return redirect('accounts_receivable')



def manage_accounts_payable(request):
    accounts=AccountsPayable.objects.all()
    context={
        'accounts':accounts
    }
    return render(request, 'IMS_admin/accounts_payable_table.html', context)

def purchase_order_detail(request):
    return HttpResponse("Accounts Payable page")

def edit_purchase(request):
    return HttpResponse("Accounts Payable page")

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


