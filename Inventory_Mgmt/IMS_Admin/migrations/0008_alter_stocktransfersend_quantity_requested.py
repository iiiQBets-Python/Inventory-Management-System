# Generated by Django 5.1 on 2024-08-26 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IMS_Admin', '0007_stocktransferreceive_damaged_stock_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stocktransfersend',
            name='quantity_requested',
            field=models.IntegerField(),
        ),
    ]
