from django.contrib import admin

from .models import *

admin.site.register(Department)
admin.site.register(Employee)
admin.site.register(manufacturer)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Customer)
admin.site.register(warehouse)
admin.site.register(Order)
admin.site.register(OrderDetail)
admin.site.register(invoice)
admin.site.register(invoice_items)
admin.site.register(Company_details)

