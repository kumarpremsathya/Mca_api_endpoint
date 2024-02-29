# Generated by Django 4.2.9 on 2024-02-22 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mca_app', '0005_sebi_orders'),
    ]

    operations = [
        migrations.CreateModel(
            name='mca_orders',
            fields=[
                ('sr_no', models.IntegerField(primary_key=True, serialize=False)),
                ('date_of_order', models.CharField(default=None, max_length=255, null=True)),
                ('title_of_order', models.CharField(default=None, max_length=255, null=True)),
                ('type_of_order', models.CharField(default=None, max_length=255, null=True)),
                ('ROC_RD', models.CharField(default=None, max_length=255, null=True)),
                ('link_to_order', models.CharField(default=None, max_length=955, null=True)),
                ('pdf_file_path', models.CharField(default=None, max_length=255, null=True)),
                ('pdf_file_name', models.CharField(default=None, max_length=255, null=True)),
                ('updated_date', models.CharField(default=None, max_length=255, null=True)),
                ('date_scraped', models.DateTimeField(default=models.DateTimeField(auto_now_add=True))),
            ],
            options={
                'db_table': 'mca_orders',
            },
        ),
        migrations.DeleteModel(
            name='rbi_odi',
        ),
        migrations.AlterModelTable(
            name='sebi_orders',
            table='sebi_orders',
        ),
    ]
