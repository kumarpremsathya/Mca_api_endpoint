# Generated by Django 4.2.9 on 2024-02-27 12:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mca_app', '0006_mca_orders_delete_rbi_odi_alter_sebi_orders_table'),
    ]

    operations = [
        migrations.DeleteModel(
            name='sebi_orders',
        ),
    ]
