from django.db import models
from django.contrib.auth.models import User
  

        
class mca_orders(models.Model):
    sr_no = models.IntegerField(primary_key=True)
    title_of_order = models.CharField(max_length=255, default=None, null=True)
    type_of_order = models.CharField(max_length=255, default=None, null=True)
    ROC_RD = models.CharField(max_length=255, default=None, null=True)
    date_of_order = models.CharField(max_length=255, default=None, null=True)
    link_to_order = models.CharField(max_length=955, default=None, null=True)
    pdf_file_path = models.CharField(max_length=255, default=None, null=True)
    pdf_file_name = models.CharField(max_length=255, default=None, null=True)
    updated_date= models.CharField(max_length=255, default=None, null=True)
    date_scraped = models.DateTimeField(default=models.DateTimeField(auto_now_add=True))
    
    class Meta:
        db_table='mca_orders'