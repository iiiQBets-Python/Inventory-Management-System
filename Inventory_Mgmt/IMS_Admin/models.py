from datetime import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.utils import timezone


class Department(models.Model):
    id = models.CharField(max_length=25, unique=True, primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Employee(models.Model):
    gender = models.CharField(max_length=10, null=True)
    First_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    date_of_birth = models.DateField()
    email = models.EmailField()
    address = models.TextField()
    phone_number = models.IntegerField()
    designation = models.CharField(max_length=25)
    date_of_joining = models.DateField()
    image = models.ImageField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, to_field='id')
    password = models.CharField(max_length=25)

    def __str__(self):
        return self.First_name

    def save(self, *args, **kwargs):
        self.password = make_password(self.password)
        super(Employee, self).save(*args, **kwargs)



class Supplier(models.Model):
    BUSINESS_TYPES = (
        ('Private Limited Company', 'Private Limited Company'),
        ('Public Limited Company', 'Public Limited Company'),
        ('Partnership', 'Partnership'),
        ('Sole Proprietorship', 'Sole Proprietorship'),
        ('Limited Liability Partnership (LLP)', 'Limited Liability Partnership (LLP)')
    )

    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    contact_number = models.CharField(max_length=15)
    gstin_number = models.CharField(max_length=15)
    pan_number = models.CharField(max_length=10)
    address = models.TextField()
    bank_account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES)
    business_license_number = models.CharField(max_length=50)
    is_manufacturer = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.CharField(max_length=10, unique=True, primary_key=True)
    name = models.CharField(max_length=25)
    def __str__(self):
        return self.name

class Brand(models.Model):
    id = models.CharField(max_length=10, unique=True, primary_key=True)
    name = models.CharField(max_length=25)
    def __str__(self):
        return self.name

class Product(models.Model):
    product_id = models.CharField(max_length=10, unique=True, primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, to_field="id")
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, default="Piece")
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight_unit = models.CharField(max_length=10, default="kg")
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dimension_unit = models.CharField(max_length=10, default="cm")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, to_field="id")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, to_field="id")
    hsn_code = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    description = models.TextField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.product_name
    


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    pan_no = models.CharField(max_length=10)
    aadhar_no = models.CharField(max_length=12)
    email = models.EmailField()
    mobile_no = models.CharField(max_length=15)
    current_address = models.TextField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)
    customer_id = models.CharField(max_length=10)
    gst_no = models.CharField(max_length=15)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    sales_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    def save(self, *args, **kwargs):
        if self.sales_employee:
            self.sales_employee_id = self.sales_employee.id
        super(Customer, self).save(*args, **kwargs)

class Warehouse(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Name of the warehouse
    location = models.TextField()  # Location/address of the warehouse
    capacity = models.IntegerField()  # Capacity of the warehouse (e.g., max number of units it can store)
    current_stock = models.IntegerField(default=0)  # Current stock level in the warehouse
    manager_name = models.ForeignKey(Employee, on_delete=models.CASCADE)  # Name of the warehouse manager
    manager_contact = models.CharField(max_length=20)  # Contact number of the manager
    email = models.EmailField(null=True, blank=True)  # Email of the manager
    contact_number = models.CharField(max_length=20, null=True, blank=True)  # Main contact number for the warehouse
    notes = models.TextField(null=True, blank=True)  # Additional notes or comments about the warehouse

    def available_capacity(self):
        # Return the remaining available capacity in the warehouse
        return self.capacity - self.current_stock

    def __str__(self):
        return f"{self.name} - {self.location}"

    def clean(self):
        # Ensure that the current stock does not exceed the capacity
        if self.current_stock > self.capacity:
            raise ValidationError('Current stock cannot exceed warehouse capacity.')

    def save(self, *args, **kwargs):
        # Perform validation before saving the model
        self.clean()
        super(Warehouse, self).save(*args, **kwargs)

class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, to_field='id')
    product= models.ForeignKey(Product, on_delete=models.CASCADE)
    stock_status = models.BooleanField(default=True, verbose_name="Stock Status (In Stock)")
    stock_number = models.IntegerField(default=0, verbose_name="Stock Number")
    low_stock_threshold = models.IntegerField(default=10)

    def check_low_stock(self):
        if self.stock_number < self.low_stock_threshold:
            return True
        return False

    def __str__(self):
        return f"{self.product.product_name} - {self.warehouse.name}"

class Restock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE)
    quantity_added = models.PositiveIntegerField()
    restocked_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    restocked_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Restocked {self.quantity_added} units of {self.product.product_name} at {self.warehouse.name} by {self.restocked_by}"

class StockTransferRequest(models.Model):
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='outgoing_requests')
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='incoming_requests')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending')
    request_date = models.DateTimeField(auto_now_add=True)
    fulfilled_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Transfer of {self.quantity} {self.product.product_name} from {self.source_warehouse.name} to {self.destination_warehouse.name}"

class StockTransferSend(models.Model):
    transfer_request = models.ForeignKey(StockTransferRequest, on_delete=models.CASCADE, related_name='sends')
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='outgoing_transfers')
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='incoming_transfers')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_requested = models.IntegerField()
    quantity_sent = models.PositiveIntegerField()
    send_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sent {self.quantity_sent} units of {self.product.product_name} from {self.source_warehouse.name}"

class StockTransferReceive(models.Model):
    transfer_request = models.ForeignKey(StockTransferSend, on_delete=models.CASCADE, related_name='receives')
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='incoming_stock')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_send = models.PositiveIntegerField()
    damaged_stock = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField()
    receive_date = models.DateTimeField(auto_now_add=True)
    discrepancy_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Received {self.quantity_received} units of {self.product.product_name} at {self.destination_warehouse.name}"


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateField(auto_now_add=True)
    sales_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_generated=models.BooleanField(default=False)

    

from django.core.exceptions import ValidationError
from django.db import models

class OrderDetail(models.Model):
    TAX_TYPES = [
        ('ST', 'Sales Tax'),
        ('VAT', 'Value Added Tax'),
        ('ET', 'Excise Tax'),
        ('GST', 'Goods and Services Tax'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    tax_type = models.CharField(max_length=50, choices=TAX_TYPES)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, editable=False)

    def net_amount(self):
        return (self.unit_price * self.quantity) - self.discount

    def tax_amount(self):
        return (self.net_amount() * self.tax_rate) / 100

    def total_amount(self):
        return self.net_amount() + self.tax_amount()

    def save(self, *args, **kwargs):
        if not self.tax_rate:
            if self.tax_type == 'ST':
                self.tax_rate = 10
            elif self.tax_type == 'VAT':
                self.tax_rate = 15
            elif self.tax_type == 'ET':
                self.tax_rate = 5
            elif self.tax_type == 'GST':
                self.tax_rate = 18

        super(OrderDetail, self).save(*args, **kwargs)

    

class Invoice(models.Model):
    order_id=models.ForeignKey(Order, on_delete=models.CASCADE)
    customer=models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice_date=models.DateField()
    due_date=models.DateField()
    
    total_amount=models.DecimalField(max_digits=15, decimal_places=3, editable=False)


class Invoice_items(models.Model):
    invoice_id=models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product_name=models.ForeignKey(Product, on_delete=models.CASCADE)
    cost_price=models.CharField(max_length=10)
    selling_price=models.CharField(max_length=10)
    net_amount=models.CharField(max_length=10)
    quantity=models.IntegerField()
    tax_type=models.CharField(max_length=25)
    tax_rate=models.DecimalField(max_digits=15, decimal_places=3, editable=False, null=True)
    tax_amount=models.DecimalField(max_digits=15, decimal_places=3, editable=False, null=True)
    discount=models.DecimalField(max_digits=15, decimal_places=3, editable=False, null=True)
    description=models.CharField(max_length=250)


class Company_details(models.Model):
    name=models.CharField(max_length=50)
    email=models.EmailField()
    gst_no=models.CharField(max_length=25,unique=True)
    pan_no=models.CharField(max_length=10,unique=True)
    address=models.TextField()
    pincode=models.IntegerField()
    phone_number=models.IntegerField()
    tc1=models.CharField(max_length=50, null=True)
    password = models.CharField(max_length=50, null=False)
    
    def __str__(self):
        return self.name
    

    
class PurchaseOrder(models.Model):
    PO_STATUS = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    expected_delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=PO_STATUS, default='Pending')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"PO-{self.id} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.product.product_name} - {self.purchase_order.id}"
    

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class AccountsReceivable(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Partially Paid', 'Partially Paid'),
        ('Overdue', 'Overdue'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Online Transfer', 'Online Transfer'),
        ('Cheque', 'Cheque'),
    ]

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)  # Renamed from amount_due
    balance_due = models.DecimalField(max_digits=15, decimal_places=2)  # Remaining balance
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def save(self, *args, **kwargs):
        """ Update balance_due and ensure the status is updated based on payment amounts before saving. """
        if self.amount_paid >= self.total_amount:
            self.status = 'Paid'
        elif self.amount_paid > 0 and self.amount_paid < self.total_amount:
            self.status = 'Partially Paid'
        if self.due_date < timezone.now().date() and self.balance_due > 0:
            self.status = 'Overdue'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice.id} - {self.customer}"
    

class AccountsPayable(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Partially Paid', 'Partially Paid'),   
        ('Overdue', 'Overdue'),
    ]

    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE)
    total_payable_amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_due = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

class Meta:
    indexes = [
        models.Index(fields=['status']),
        models.Index(fields=['due_date']),
    ]

def _str_(self):
    return f"Payable: {self.purchase_order.id} - {self.supplier.name}"

@property
def balance_due(self):
    return self.amount_due - self.amount_paid

def clean(self):
    if self.amount_paid > self.amount_due:
        raise ValidationError('Amount paid cannot exceed the amount due.')

def save(self, *args, **kwargs):
    # Automatically update status based on amounts and due date
    if self.amount_paid >= self.amount_due:
        self.status = 'Paid'
        if not self.payment_date:
            self.payment_date = timezone.now().date()
    elif self.amount_paid > 0:
        self.status = 'Partially Paid'
    elif self.due_date < timezone.now().date() and self.status == 'Pending':
        self.status = 'Overdue'

    super().save(*args, **kwargs)