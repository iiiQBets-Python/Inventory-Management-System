# Generated by Django 5.1 on 2024-08-23 09:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IMS_Admin', '0003_rename_product_name_stock_product_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='warehouse',
            name='manager_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='IMS_Admin.employee'),
        ),
    ]
