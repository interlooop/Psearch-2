# Generated by Django 3.2.4 on 2022-02-12 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_auto_20220212_2301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='qtyInStock',
            field=models.IntegerField(blank=True, default=10, null=True),
        ),
    ]
