from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

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

class manufacturer(models.Model):
    BUSINESS_TYPES = (
        ('Private Limited Company', 'Private Limited Company'),
        ('Public Limited Company', 'Public Limited Company'),
        ('Partnership', 'Partnership'),
        ('Sole Proprietorship', 'Sole Proprietorship'),
        ('Limited Liability Partnership (LLP)', 'Limited Liability Partnership (LLP)')
    )

    Company_Name = models.CharField(max_length=100, unique=True)
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

    def __str__(self):
        return self.Company_Name

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
    manufacturer = models.ForeignKey(manufacturer, on_delete=models.CASCADE, to_field="id")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, to_field="id")
    upc = models.CharField(max_length=255, unique=True)
    ean = models.CharField(max_length=255, unique=True)
    mpn = models.CharField(max_length=255, unique=True)
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

class warehouse(models.Model):
    manufacturer = models.ForeignKey(manufacturer, on_delete=models.CASCADE, to_field='Company_Name')
    upc = models.CharField(max_length=255, null=True, blank=True, verbose_name="UPC (Universal Product Code)")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, to_field='id')
    mpn = models.CharField(max_length=255, null=True, blank=True, verbose_name="MPN (Manufacturer Part Number)")
    product_name = models.ForeignKey(Product, on_delete=models.CASCADE)
    ean = models.CharField(max_length=255, null=True, blank=True, verbose_name="EAN (European Article Number)")
    stock_status = models.BooleanField(default=True, verbose_name="Stock Status (In Stock)")
    stock_number = models.IntegerField(default=0, verbose_name="Stock Number")
    

    

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
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

        self.adjust_warehouse_stock()
        super(OrderDetail, self).save(*args, **kwargs)

    def adjust_warehouse_stock(self):
        warehouse_product = warehouse.objects.filter(upc=self.product.upc).first()
        
        if not warehouse_product:
            raise ValidationError(f"Product not found in warehouse: {self.product.product_name}")

        if self.pk:
            previous_instance = OrderDetail.objects.get(pk=self.pk)
            previous_quantity = previous_instance.quantity
            warehouse_product.stock_number += previous_quantity

        if warehouse_product.stock_number >= self.quantity:
            warehouse_product.stock_number -= self.quantity
            warehouse_product.save()
        else:
            raise ValidationError(f"Not enough stock available for product: {self.product.product_name}")

class invoice(models.Model):
    order_id=models.ForeignKey(Order, on_delete=models.CASCADE)
    customer=models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice_date=models.DateField()
    due_date=models.DateField()
    
    total_amount=models.DecimalField(max_digits=15, decimal_places=3, editable=False)


class invoice_items(models.Model):
    invoice_id=models.ForeignKey(invoice, on_delete=models.CASCADE)
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


