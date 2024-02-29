#mca api end point
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import *
from datetime import datetime
from django.http import Http404
import zipfile
from io import BytesIO
from django.shortcuts import render, HttpResponse
import json
from django.http import request

from django.http import HttpResponse
import json
import zipfile
from io import BytesIO
from django.urls import reverse
from django.views import View
import io
import csv

from django.http import HttpResponse
import zipfile
from io import BytesIO
from django.views import View
from .models import mca_orders
from django.core.serializers.json import DjangoJSONEncoder


from rest_framework import renderers
from django.core.exceptions import ValidationError
# from django.core.validators import validate_date
from django.db.models import Q

import os
from django.conf import settings
import calendar
import datetime       
   
import zipfile
from django.views import View
from rest_framework import status
# from .models import sebi_orders        
from datetime import datetime

from pathlib import Path   
import tempfile



# Define the custom HTML renderer
class HTMLRenderer(renderers.BaseRenderer):
    media_type = 'text/html'
    format = 'html'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        html_content = '<html><body>'
        for entry in data['result']:
            html_content += f'<p>Date: {entry["date_of_order"]}</p>'
            html_content += f'<p>Title: {entry["title_of_order"]}</p>'
            html_content += f'<p>Type Of Order: {entry["type_of_order"]}</p>'
            html_content += f'<p>Link to Order: {entry["link_to_order"]}</p>'
            html_content += f'<p>PDF File Path: {entry["pdf_file_path"]}</p>'
            html_content += f'<p>PDF File Name: {entry["pdf_file_name"]}</p>'
            html_content += f'<p>Date Scraped: {entry["date_scraped"]}</p>'
            html_content += '<hr />'
            
         # Add the total PDF download link to the HTML content
        html_content += f'<p>Total Count: {data["total_count"]}</p>' 
        html_content += f'<p>{data["total_pdf_download_link"]}</p>'    
        html_content += '</body></html>'
        return html_content.encode(self.charset)





def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except:
       return False

class Custom404View(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"result": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)
        

# # Define your API view
class GetOrderDateView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
        except ValueError:
            return Response({"result": "Invalid limit or offset value, must be an integer"}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)

        date = str(request.GET.get('date', None))
        type_of_order = kwargs.get('type_of_order')  # Extract 'type_of_order' parameter from URL

        if date:
            if len(date) != 10 or not validate_date(date):
                return Response({"result": "Incorrect date format, should be YYYY-MM-DD"}, status = status.HTTP_422_UNPROCESSABLE_ENTITY)



            valid_parameters = {'limit', 'offset', 'date'}
            provided_parameters = set(request.GET.keys())

            if not valid_parameters.issuperset(provided_parameters):
                return Response({"result": "Invalid query parameters, check spelling for given parameters"}, status = status.HTTP_400_BAD_REQUEST)
            
            try:
                # Filter queryset based on 'type_of_order' parameter
                if type_of_order == 'RD':
                    order_details = mca_orders.objects.filter(date_scraped__startswith=date, type_of_order='RD').values( 'title_of_order', 'type_of_order', 'ROC_RD', 'date_of_order',  'link_to_order',  'pdf_file_path', 'pdf_file_name', 'updated_date',  'date_scraped')[offset:limit]
                    total_count = mca_orders.objects.filter(date_scraped__startswith=date, type_of_order='RD').count()
                elif type_of_order == 'ROC':
                    order_details = mca_orders.objects.filter(date_scraped__startswith=date, type_of_order='ROC').values('title_of_order', 'type_of_order', 'ROC_RD', 'date_of_order', 'link_to_order',  'pdf_file_path', 'pdf_file_name', 'updated_date',  'date_scraped')[offset:limit]
                    total_count = mca_orders.objects.filter(date_scraped__startswith=date, type_of_order='ROC').count()
                else:
                    return Response({"result": "Invalid 'type_of_order' parameter"}, status=status.HTTP_400_BAD_REQUEST)

                
                
                print(" order_details :", order_details )
                if len(order_details) > 0:
                
                    # Create download link for the zip file
                    total_pdf_download_link = request.build_absolute_uri('/api/v1/{}/download_pdfs/?date={}'.format(type_of_order, date))+ f'&limit={limit}&offset={offset}' 

                    
                    # Return JSON response with results including the total PDF download link
                    return Response({"result": order_details, 'total_count': total_count, 'total_pdf_download_link': total_pdf_download_link}, status=status.HTTP_200_OK)
                else:
                    return Response({"result": "No Data Provided in your specific date!!!."}, status = status.HTTP_401_UNAUTHORIZED)
            except TimeoutError:
                return Response({"result": "timeout error"}, status = status.HTTP_502_BAD_GATEWAY)
            except Exception as err:
                return Response({"result": f"An internal server error occurred: {err}"}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
           raise Http404("Page not found")



class DownloadPDFsView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
            
            # Check if the limit is above 500 and raise an exception if so
            if limit > 500:
                return Response({"result": "Limit should not exceed 500"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as ve:
            return Response({"result": str(ve)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        date = request.GET.get('date')
        type_of_order = kwargs.get('type_of_order')  # Extract 'type_of_order ' parameter from URL
        
        BASE_DIR2 = 'C:\\Users\\Premkumar.8265\\Desktop\\'  # Update with your base directory
        print("BASE_DIR2: ", BASE_DIR2)
        
        try:
            if date:
                try:
                    validate_date(date)
                except ValidationError:
                    return Response({"result": "Incorrect date format, should be YYYY-MM-DD"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

                valid_parameters = {'limit', 'offset', 'date'}
                provided_parameters = set(request.GET.keys())

                if not valid_parameters.issuperset(provided_parameters):
                    return Response({"result": "Invalid query parameters, check spelling for given parameters"}, status=status.HTTP_400_BAD_REQUEST)

                root_directory = os.path.join(settings.MEDIA_ROOT, type_of_order)
                print("Root directory:", root_directory)  # Check the root directory

                year, month, day = date.split('-')
                month_name = calendar.month_name[int(month)]
                print("Year:", year)  # Check the year
                print("Month:", month_name)  # Check the month name
                
                # Retrieve all orders for the specified date
                order_details = mca_orders.objects.filter(date_scraped__startswith=date, type_of_order=type_of_order)[offset:limit]

                print("order_details:", order_details)  
                
                pdf_paths = [os.path.join(BASE_DIR2, order.pdf_file_path) for order in order_details]

                print("PDF paths:", pdf_paths)  # Check the PDF paths
                
                if pdf_paths:
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    with zipfile.ZipFile(temp_file, 'w') as zip_file:
                        for pdf_path in pdf_paths:
                            if os.path.exists(pdf_path):
                                zip_file.write(pdf_path, os.path.relpath(pdf_path, BASE_DIR2))
                            else:
                                # If the PDF file is missing, log an error or return a message
                                print("Error: The file does not exist:", pdf_path)
                                return Response({"result": f"PDF file {pdf_path} is missing"}, status=status.HTTP_404_NOT_FOUND)

                    temp_file.close()
                    temp_file = open(temp_file.name, 'rb')
                    data = temp_file.read()
                    temp_file.close()
                    os.unlink(temp_file.name)
                    
                    response = HttpResponse(data, content_type='application/zip')
                    response['Content-Disposition'] = 'attachment; filename="Mca_pdf_files.zip"'
                    
                    return response
                else:
                    return HttpResponse("No PDF files found for the specified date.", status=status.HTTP_404_NOT_FOUND)
            else:
                return HttpResponse("Date parameter is required.", status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return HttpResponse("Invalid limit or offset value, must be an integer", status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValidationError:
            return HttpResponse("Incorrect date format, should be YYYY-MM-DD", status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            print("Error:", e)  # Debugging statement
            return HttpResponse("An error occurred.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)



   
# class DownloadPDFsView(APIView):
#     def get(self, request, *args, **kwargs):
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
            
#             # Check if the limit is above 500 and raise an exception if so
#             if limit > 500:
#                 raise ValueError("Limit should not exceed 500")
#         except ValueError as ve:
#             return Response({"result": str(ve)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

#         date = str(request.GET.get('date', None))
#         type_of_order = kwargs.get('type_of_order')  # Extract 'type_of_order ' parameter from URL
        
        
#         # Build paths inside the project like this: BASE_DIR2 / 'subdir'.
#         BASE_DIR2 = 'C:\\Users\\Premkumar.8265\\Desktop\\'
#         print("BASE_DIR2: ", BASE_DIR2)
        
#         try:
#             if date:
#                 try:
#                     validate_date(date)
#                 except ValidationError:
#                     return Response({"result": "Incorrect date format, should be YYYY-MM-DD"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

#                 valid_parameters = {'limit', 'offset', 'date'}
#                 provided_parameters = set(request.GET.keys())

#                 if not valid_parameters.issuperset(provided_parameters):
#                     return Response({"result": "Invalid query parameters, check spelling for given parameters"}, status=status.HTTP_400_BAD_REQUEST)

#                 # Define the root directory based on type_of_order
#                 root_directory = os.path.join(settings.MEDIA_ROOT, type_of_order)
#                 print("root_directory : ", root_directory)
                 
#                # Extract year and month from the date
#                 year, month, _ = date.split('-')
                
#                 # Get the month name from the month number
#                 month_name = calendar.month_name[int(month)]

#                 # Construct the directory path based on date
#                 directory_path = os.path.join(root_directory, year, month_name)
#                 print("directory_path : ", directory_path)
                
#                 # Check if the directory exists
#                 if not os.path.exists(directory_path):
#                     return Response("Directory not found.", status=404)

#                 # Query the necessary number of PDFs based on both limit and offset parameters
#                 order_details = mca_orders.objects.filter(date_scraped__startswith=date, type_of_order=type_of_order).values('pdf_file_name')[offset:limit]
#                 print("order_details : ", order_details)

#                 # Filter the PDFs based on sr_no values
#                 pdf_paths = [os.path.join(directory_path, entry['pdf_file_name']) for entry in order_details if entry['pdf_file_name']]
#                 print("pdf_paths : ", pdf_paths)
                
#                 if pdf_paths:
#                     # Create an HttpResponse object with content type as zip
#                     response = HttpResponse(content_type='application/zip')

#                     # Set the zip file name
#                     response['Content-Disposition'] = 'attachment; filename="Sebi_pdf_files.zip"'
                    
                    
#                     # Create a zip file
#                     with zipfile.ZipFile(response, 'w') as zip_file:
#                         # Add each PDF file to the zip
#                         for pdf_path in pdf_paths:
#                             pdf_file = os.path.join(settings.MEDIA_ROOT, pdf_path + '.pdf')  # Append .pdf if not already present
#                             if os.path.exists(pdf_file):
#                                 zip_file.write(pdf_file, arcname=os.path.basename(pdf_file))
                    
#                                 print("zip_file : ", zip_file)
#                             else:
#                                 # If the PDF file is missing, log an error or return a message
#                                 print(f"PDF file {pdf_file} is missing from the media folder")                                     # You can log this error or return a response indicating the missing file # For example, you can 
#                                 return Response({"result": f"PDF file {pdf_file} is missing"}, status=status.HTTP_404_NOT_FOUND)
#                     return response
#                 else:
#                     # If no PDF files were found, return an empty response
#                     return HttpResponse("No PDF files found.", status=404)
#             else:
#                 return HttpResponse("Date parameter is required.", status=status.HTTP_400_BAD_REQUEST)
#         except ValueError:
#             return HttpResponse("Invalid limit or offset value, must be an integer", status=status.HTTP_422_UNPROCESSABLE_ENTITY)
#         except ValidationError:
#             return HttpResponse("Incorrect date format, should be YYYY-MM-DD", status=status.HTTP_422_UNPROCESSABLE_ENTITY)
#         except Exception as e:
#             print("Error:", e)  # Debugging statement
#             return HttpResponse("An error occurred.", status=500)

           
  
  
class DownloadSinglePDFView(View):
    def get(self, request, filename):
        pdf_path = os.path.join(settings.MEDIA_ROOT, filename)
        # 

        if os.path.exists(pdf_path):
            response = HttpResponse(content_type='application/zip')
            zip_file = zipfile.ZipFile(response, 'w')

            # Add the PDF file to the ZIP archive
            zip_file.write(pdf_path, os.path.basename(pdf_path))

            # Close the ZIP file
            zip_file.close()

            # Set the appropriate content-disposition header for the response
            response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'
            return response
        else:
            # Handle case when PDF file doesn't exist
            return HttpResponse("PDF file not found.", status=404)
         
  
  
        
 
def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

class Custom404View(APIView):
    def get(self, request, *args, **kwargs):
        return Response({"result": "Resource not found", 'status': status.HTTP_404_NOT_FOUND})


#function for querying the endpoint using year and month and date on which pdfs are updated in websites, here month and date are optioanl.


class GetOrderYearView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
            year = request.GET.get('year')
            month = request.GET.get('month')
            date = request.GET.get('date')
            
            if date:
                print("Original date:", date)
                date = date.zfill(2)
                print("Formatted date:", date)
                
        except ValueError:
            return Response({"result": "Invalid limit or offset value, must be an integer", 'status':status.HTTP_422_UNPROCESSABLE_ENTITY})

        type_of_order = kwargs.get('type_of_order')

        valid_parameters = {'limit', 'offset', 'year', 'month', 'date'}
        provided_parameters = set(request.GET.keys())

        if not valid_parameters.issuperset(provided_parameters):
            return Response({"result": "Invalid query parameters, check spelling for given parameters", 'status': status.HTTP_400_BAD_REQUEST})

        try:
            queryset = mca_orders.objects.filter(type_of_order=type_of_order)

            if year:
                queryset = queryset.filter(date_of_order__icontains=year)

            if month:
                # Convert the month name to its abbreviation
                queryset = queryset.filter(date_of_order__icontains=month)
                # month_abbr = datetime.strptime(month, '%m').strftime('%b')
                # queryset = queryset.filter(date_of_order__contains=f"{month_abbr}")

            if date:
                 # Ensure single-digit dates are formatted with a leading zero
                date = date.zfill(2)
                print("Filtering by date:", date)
                queryset = queryset.filter(
                      Q(date_of_order__exact=date)  # Match for '02' as a standalone date
                )
                print(queryset.query)
                print("queryset:", queryset)

            order_details = queryset.values( 'title_of_order', 'type_of_order', 'ROC_RD', 'date_of_order', 'link_to_order', 'pdf_file_path', 'pdf_file_name', 'updated_date', 'date_scraped')[offset:limit]
            print("order_details:", order_details)
            total_count = queryset.count()

            if len(order_details) > 0:
                total_pdf_download_link = request.build_absolute_uri(f'/api/v1/{type_of_order}/download_all_pdfs/?year={year}&month={month}&date={date}&limit={limit}&offset={offset}') 
                
                return Response({"result": order_details, 'total_count': total_count, 'total_pdf_download_link': total_pdf_download_link}, status=status.HTTP_200_OK)
            else:
                return Response({"result": "No Data Provided in your specific date", 'status': status.HTTP_401_UNAUTHORIZED})
        except TimeoutError:
            return Response({"result": "timeout error", 'status': status.HTTP_502_BAD_GATEWAY})
        except Exception as err:
            return Response({"result": f"An internal server error occurred: {err}", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})
        
 

class DownloadAllPDFsView(View):
    def get(self, request, *args, **kwargs):
        try:
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
            year = request.GET.get('year')
            month = request.GET.get('month')
            date = request.GET.get('date')
            type_of_order = kwargs.get('type_of_order')
        except ValueError:
            return HttpResponse("Invalid limit or offset value, must be an integer", status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            queryset = mca_orders.objects.filter(type_of_order=type_of_order)

            if year:
                queryset = queryset.filter(date_of_order__icontains=year)

            if month:
                queryset = queryset.filter(date_of_order__icontains=month)
                # month_abbr = datetime.strptime(month, '%m').strftime('%b')
                # queryset = queryset.filter(date_of_order__contains=f"{month_abbr}")

                
            if date: # Check if date is provided and not 'None'
                queryset = queryset.filter(date_of_order__contains=date)

            
            # Filter the PDFs based on sr_no values
            pdf_paths = [os.path.join(settings.MEDIA_ROOT, entry['pdf_file_name']) for entry in queryset  if entry['pdf_file_name']]
                    
            print("pdf_paths :", pdf_paths)

            if pdf_paths:
                response = HttpResponse(content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="Mca_pdf_files.zip"'

                with zipfile.ZipFile(response, 'w') as zip_file:
                    for pdf_path in pdf_paths[offset:offset+limit]:
                        pdf_file = os.path.join(settings.MEDIA_ROOT, pdf_path)
                        if os.path.exists(pdf_file):
                            zip_file.write(pdf_file, arcname=os.path.basename(pdf_file))

                return response
            else:
                return HttpResponse("No PDF files found.", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("Error:", e)
            return HttpResponse("An error occurred.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
# class GetOrderdateView(APIView):
#     def get(self, request, *args, **kwargs):
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
#         except ValueError:
#             return Response({"result": "Invalid limit or offset value, must be an integer"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

#         date = str(request.GET.get('date', None))
#         whether = kwargs.get('whether')  # Extract 'whether' parameter from URL

#         if date:
#             try:
#                 validate_date(date)
#             except ValidationError:
#                 return Response({"result": "Incorrect date format, should be YYYY-MM-DD"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

#             valid_parameters = {'limit', 'offset', 'date'}
#             provided_parameters = set(request.GET.keys())

#             if not valid_parameters.issuperset(provided_parameters):
#                 return Response({"result": "Invalid query parameters, check spelling for given parameters"}, status=status.HTTP_400_BAD_REQUEST)

#             # Filter queryset based on 'whether' parameter
#             if whether == 'ed_cgm':
#                 order_details = sebi_orders.objects.filter(date_scraped__startswith=date, type_of_order='ed_cgm').values('sr_no', 'date_of_order',  'title_of_order', 'type_of_order', 'link_to_order',  'pdf_file_path', 'pdf_file_name', 'updated_date',  'date_scraped')[offset:limit]
#             elif whether == 'ao_cgm':
#                 order_details = sebi_orders.objects.filter(date_scraped__startswith=date, type_of_order='ao_cgm').values('sr_no', 'date_of_order',  'title_of_order', 'type_of_order', 'link_to_order',  'pdf_file_path', 'pdf_file_name', 'updated_date',  'date_scraped')[offset:limit]
#             else:
#                 return Response({"result": "Invalid 'whether' parameter"}, status=status.HTTP_400_BAD_REQUEST)

#             total_count = order_details.count()

#             if len(order_details) > 0:
#                 # Convert order_details to JSON
#                 order_details_json = json.dumps(list(order_details), default=str)

#                 # Create a BytesIO object to store zip file contents
#                 zip_buffer = BytesIO()
#                 with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
#                     # Add order_details as a JSON file in the zip archive
#                     zip_file.writestr("order_details.json", order_details_json)
                
#                 # Set the buffer's file pointer to the beginning
#                 zip_buffer.seek(0)
                
#                 # Create download link for the zip file
#                 download_zipfile = request.build_absolute_uri('/api/v1/{}/download_zip/?date={}'.format(whether, date))   # Assuming download URL is 'download/'

#                 # Return JSON response with results and download link
#                 return Response({"result": order_details, 'total_count': total_count, 'download_zipfile': download_zipfile}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"result": "No Data Provided in your specific date!!!.", 'status': status.HTTP_401_UNAUTHORIZED})
#         else:
#             raise Http404("Page not found")
          

# class GetOrderdateView(APIView):
#     def get(self, request, *args, **kwargs):
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
#         except ValueError:
#             return Response({"result": "Invalid limit or offset value, must be an integer"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

#         date = str(request.GET.get('date', None))
#         whether = kwargs.get('whether')  # Extract 'whether' parameter from URL

#         if date:
#             try:
#                 validate_date(date)
#             except ValidationError:
#                 return Response({"result": "Incorrect date format, should be YYYY-MM-DD"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

#             valid_parameters = {'limit', 'offset', 'date'}
#             provided_parameters = set(request.GET.keys())

#             if not valid_parameters.issuperset(provided_parameters):
#                 return Response({"result": "Invalid query parameters, check spelling for given parameters"}, status=status.HTTP_400_BAD_REQUEST)

#             # Filter queryset based on 'whether' parameter
#             if whether == 'WOS':
#                 order_details = rbi_odi.objects.filter(date_scraped__startswith=date, Whether_JV_WOS='WOS').values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#             elif whether == 'JV':
#                 order_details = rbi_odi.objects.filter(date_scraped__startswith=date, Whether_JV_WOS='JV').values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#             else:
#                 return Response({"result": "Invalid 'whether' parameter"}, status=status.HTTP_400_BAD_REQUEST)

#             total_count = order_details.count()

#             if len(order_details) > 0:
#                 # Convert order_details to JSON
#                 order_details_json = json.dumps(list(order_details), default=str)

#                 # Create a BytesIO object to store zip file contents
#                 zip_buffer = BytesIO()
#                 with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
#                     # Add order_details as a JSON file in the zip archive
#                     zip_file.writestr("order_details.json", order_details_json)
                
#                 # Set the buffer's file pointer to the beginning
#                 zip_buffer.seek(0)
                
#                 # Create download link for the zip file
#                 download_zipfile = request.build_absolute_uri('/api/v1/{}/download_zip/?date={}'.format(whether, date))   # Assuming download URL is 'download/'

#                 # Return JSON response with results and download link
#                 return Response({"result": order_details, 'total_count': total_count, 'download_zipfile': download_zipfile}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"result": "No Data Provided in your specific date!!!.", 'status': status.HTTP_401_UNAUTHORIZED})
#         else:
#             raise Http404("Page not found")
        
 
class DownloadZipView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
        except ValueError:
            return Response({"result": "Invalid limit or offset value, must be an integer"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        date = str(request.GET.get('date', None))
        whether = kwargs.get('whether')  # Extract 'whether' parameter from URL

        if date:
            try:
                validate_date(date)
            except ValidationError:
                return Response({"result": "Incorrect date format, should be YYYY-MM-DD"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            valid_parameters = {'limit', 'offset', 'date'}
            provided_parameters = set(request.GET.keys())

            if not valid_parameters.issuperset(provided_parameters):
                return Response({"result": "Invalid query parameters, check spelling for given parameters"}, status=status.HTTP_400_BAD_REQUEST)

            # Filter queryset based on 'whether' parameter
            if whether == 'ed_cgm':
                order_details = mca_orders.objects.filter(date_scraped__startswith=date, type_of_order='ed_cgm').values('sr_no', 'date_of_order',  'title_of_order', 'type_of_order', 'link_to_order',  'pdf_file_path', 'pdf_file_name', 'updated_date',  'date_scraped')[offset:limit]
            elif whether == 'ao_cgm':
                order_details = mca_orders.objects.filter(date_scraped__startswith=date, type_of_order='ed_cgm').values('sr_no', 'date_of_order',  'title_of_order', 'type_of_order', 'link_to_order',  'pdf_file_path', 'pdf_file_name', 'updated_date',  'date_scraped')[offset:limit]
            else:
                return Response({"result": "Invalid 'whether' parameter"}, status=status.HTTP_400_BAD_REQUEST)

            total_count = order_details.count()

            if len(order_details) > 0:
                # Create a BytesIO object to store zip file contents
                # zip_buffer = BytesIO()
                # with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                #     for entry in order_details:
                #         # Serialize entry to JSON string
                #         entry_json = json.dumps(entry, default=str)
                #         # Add entry as file in the zip archive
                #         zip_file.writestr(f"{entry['SI_NO']}.json", entry_json)
                
                # # Set the buffer's file pointer to the beginning
                # zip_buffer.seek(0)

                
                # Serialize queryset to JSON
                json_data = json.dumps(list(order_details), cls=DjangoJSONEncoder, indent=4)
                
                # Create a BytesIO object to hold the zip file in memory
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w') as zip_file:
                    # Write JSON data
                    zip_file.writestr('data.json', json_data)
                
                buffer.seek(0)
                # Prepare respons
                
                
                # Return the zip file as response
                response = HttpResponse(buffer, content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="order_details.zip"'
                return response
            else:
                return Response({"result": "No Data Provided in your specific date!!!.", 'status': status.HTTP_401_UNAUTHORIZED})
        else:
            raise Http404("Page not found")   
        
            

# class GetOrderdateView(APIView):
#     def get(self, request, *args, **kwargs):
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
#         except ValueError:
#             return Response({"result": "Invalid limit or offset value, must be an integer", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})

#         date = str(request.GET.get('date', None))
#         whether = self.kwargs.get('whether')  # Extract 'whether' parameter from URL

#         if date:
#             if not validate_date(date):
#                 return Response({"result": "Incorrect date format, should be YYYY-MM-DD", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})

#             valid_parameters = {'limit', 'offset', 'date'}
#             provided_parameters = set(request.GET.keys())

#             if not valid_parameters.issuperset(provided_parameters):
#                 return Response({"result": "Invalid query parameters, check spelling for given parameters", 'status': status.HTTP_400_BAD_REQUEST})

#             try:
#                 # Filter queryset based on 'whether' parameter
#                 if whether == 'WOS':
#                     order_details = rbi_odi.objects.filter(date_scraped__startswith=date, Whether_JV_WOS='WOS').values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#                     total_count = rbi_odi.objects.filter(date_scraped__startswith=date, Whether_JV_WOS='WOS').count()
#                 elif whether == 'JV':
#                     order_details = rbi_odi.objects.filter(date_scraped__startswith=date, Whether_JV_WOS='JV').values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#                     total_count = rbi_odi.objects.filter(date_scraped__startswith=date, Whether_JV_WOS='JV').count()
#                 else:
#                     return Response({"result": "Invalid 'whether' parameter", 'status': status.HTTP_400_BAD_REQUEST})

#                 if len(order_details) > 0:
#                     return Response({"result": order_details, 'total_count': total_count, 'status': status.HTTP_200_OK})
#                 else:
#                     return Response({"result": "No Data Provided in your specific date!!!.", 'status': status.HTTP_401_UNAUTHORIZED})
#             except TimeoutError:
#                 return Response({"result": "timeout error", 'status': status.HTTP_502_BAD_GATEWAY})
#             except Exception as err:
#                 return Response({"result": f"An internal server error occurred: {err}", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})
#         else:
#             raise Http404("Page not found")

 
    
# class GetOrderdateView(APIView):
#     # permission_classes = (IsAuthenticated,)
    
#     def get(self, request):
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
#             date = request.GET.get('date')
#             whether = request.GET.get('whether')  # New parameter

#             if not validate_date(date):
#                 return Response({"result": "Incorrect date format, should be YYYY-MM-DD", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})
            
#             if whether not in ['WOS', 'JV']:
#                 return Response({"result": "Invalid 'whether' parameter", 'status': status.HTTP_400_BAD_REQUEST})
            
#             valid_parameters = {'limit', 'offset', 'date', 'whether'}
#             provided_parameters = set(request.GET.keys())

#             if not valid_parameters.issuperset(provided_parameters):
#                 return Response({"result": "Invalid query parameters, check spelling for given parameters", 'status': status.HTTP_400_BAD_REQUEST})

#             # Filter queryset based on 'whether' parameter
#             if whether == 'WOS':
#                 order_details = rbi_odi.objects.filter(date_scraped__startswith=date, Whether_JV_WOS='WOS').values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#             elif whether == 'JV':
#                 order_details = rbi_odi.objects.filter(date_scraped__startswith=date, Whether_JV_WOS='JV').values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
            
#             total_count = order_details.count()
#             for entry in order_details:
#                 for key, value in entry.items():
#                     if value == "":
#                         entry[key] = "Null"
#             if len(order_details) > 0:
#                 return Response({"result": order_details, 'total_count': total_count, 'status': status.HTTP_200_OK})
#             else:
#                 return Response({"result": "No Data Provided in your specific date!!!.", 'status': status.HTTP_401_UNAUTHORIZED})
        
#         except TimeoutError:
#             return Response({"result": "timeout error", 'status': status.HTTP_502_BAD_GATEWAY})
#         except Exception as err:
#             return Response({"result": f"An internal server error occurred: {err}", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})


        
class zipdownload(APIView):
    # permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 50))
            offset = int(request.GET.get('offset', 0))
        except ValueError:
            return Response({"result": "Invalid limit or offset value, must be an integer", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})

        date = str(request.GET.get('date', None))

        if date:
            if not validate(date):
                return Response({"result": "Incorrect date format, should be YYYY-MM-DD", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})
            
            valid_parameters = {'limit', 'offset', 'date'}
            provided_parameters = set(request.GET.keys())

            if not valid_parameters.issuperset(provided_parameters):
                return Response({"result": "Invalid query parameters, check spelling for given parameters", 'status': status.HTTP_400_BAD_REQUEST})

            try:
                order_details = mca_orders.objects.filter(date_scraped__startswith=date).values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
                
                # Convert datetime objects to strings
                for entry in order_details:
                    entry['date_scraped'] = entry['date_scraped'].strftime('%Y-%m-%d %H:%M:%S')
                
                total_count = mca_orders.objects.filter(date_scraped__startswith=date).count()
                
                # Serialize queryset to JSON
                json_data = json.dumps(list(order_details), cls=DjangoJSONEncoder, indent=4)
                
                # Create a BytesIO object to hold the zip file in memory
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w') as zip_file:
                    # Write JSON data
                    zip_file.writestr('data.json', json_data)
                
                buffer.seek(0)
                # Prepare response for downloading the zip file
                response = HttpResponse(buffer, content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="data.zip"'
                return response

            except TimeoutError:
                return Response({"result": "timeout error", 'status': status.HTTP_502_BAD_GATEWAY})
            except Exception as err:
                return Response({"result": f"An internal server error occurred: {err}", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})
        else:
            raise Http404("Page not found")




# class downloadzip1(APIView):
#     # permission_classes = (IsAuthenticated,)
    
#     def get(self, request):
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
#         except ValueError:
#             return Response({"result": "Invalid limit or offset value, must be an integer", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})

#         date = str(request.GET.get('date', None))

#         if date:
#             if not validate(date):
#                 return Response({"result": "Incorrect date format, should be YYYY-MM-DD", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})
            
#             valid_parameters = {'limit', 'offset', 'date'}
#             provided_parameters = set(request.GET.keys())

#             if not valid_parameters.issuperset(provided_parameters):
#                 return Response({"result": "Invalid query parameters, check spelling for given parameters", 'status': status.HTTP_400_BAD_REQUEST})

#             try:
#                 order_details = rbi_odi.objects.filter(date_scraped__startswith=date).values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#                 total_count = rbi_odi.objects.filter(date_scraped__startswith=date).count()
                
#                 # Create a BytesIO object to hold the zip file in memory
#                 buffer = io.BytesIO()
#                 with zipfile.ZipFile(buffer, 'w') as zip_file:
#                     # Create a CSV file in the zip for the data
#                     csv_data = io.StringIO()
#                     csv_writer = csv.writer(csv_data)
#                     csv_writer.writerow(order_details[0].keys())  # Write header
#                     for entry in order_details:
#                         csv_writer.writerow(entry.values())
#                     zip_file.writestr('data.csv', csv_data.getvalue())
                
#                 buffer.seek(0)
#                 # Prepare response for downloading the zip file
#                 response = HttpResponse(buffer, content_type='application/zip')
#                 response['Content-Disposition'] = 'attachment; filename="data.zip"'
#                 return response

#             except TimeoutError:
#                 return Response({"result": "timeout error", 'status': status.HTTP_502_BAD_GATEWAY})
#             except Exception as err:
#                 return Response({"result": f"An internal server error occurred: {err}", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})
#         else:
#             raise Http404("Page not found")
        


# class zipdownload(APIView):
#     # permission_classes = (IsAuthenticated,)
    
#     def get(self, request):
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
#         except ValueError:
#             return Response({"result": "Invalid limit or offset value, must be an integer", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})

#         date = str(request.GET.get('date', None))

#         if date:
#             if not validate(date):
#                 return Response({"result": "Incorrect date format, should be YYYY-MM-DD", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})
#             valid_parameters = {'limit', 'offset', 'date'}
#             provided_parameters = set(request.GET.keys())

#             if not valid_parameters.issuperset(provided_parameters):
#                 return Response({"result": "Invalid query parameters, check spelling for given parameters", 'status': status.HTTP_400_BAD_REQUEST})

#             try:
#                 order_details = rbi_odi.objects.filter(date_scraped__startswith=date).values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#                 total_count = rbi_odi.objects.filter(date_scraped__startswith=date).count()
                
#                 # Create a BytesIO object to store zip file contents
#                 zip_buffer = BytesIO()
#                 with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
#                     for entry in order_details:
#                         # Serialize entry to JSON string
#                         entry_json = json.dumps(entry, default=str)
#                         # Add entry as file in the zip archive
#                         zip_file.writestr(f"{entry['SI_NO']}.json", entry_json)
                
#                 # Set the buffer's file pointer to the beginning
#                 zip_buffer.seek(0)
                
#                 # Create an HTTP response with the zip file as the content
#                 response = HttpResponse(zip_buffer, content_type='application/zip')
#                 response['Content-Disposition'] = 'attachment; filename="order_details.zip"'
                
#                 # Return the HTTP response
#                 return response
            
#             except TimeoutError:
#                 return Response({"result": "timeout error", 'status': status.HTTP_502_BAD_GATEWAY})
#             except Exception as err:
#                 return Response({"result": f"An internal server error occurred: {err}", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})
#         else:
#             raise Http404("Page not found")


        
class Login(APIView):   
    # permission_classes = (AllowAny,)

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if username is None or password is None:
            return Response({'message': 'Please provide both username and password'},
                            status.HTTP_400_BAD_REQUEST)
        user = authenticate(username=username, password=password)  
        if not user:
            return Response({'status': 'Failed', 'message': 'Invalid Credentials'},
                            status.HTTP_404_NOT_FOUND)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'status': 'Success', 'token': token.key},
                        status.HTTP_200_OK)


class Logout(APIView):
    

    def get(self, request):
        request.user.auth_token.delete()
        return Response("User Logged out successfully")



def validate(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except:
        return False


# #filter date view

# class GetOrderdateView(APIView):
#     #  permission_classes = (IsAuthenticated,)
#      def get(self, request):
        
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
#         except ValueError:
#             return Response({"result": "Invalid limit or offset value, must be an integer", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})

#         date = str(request.GET.get('date', None))

#         if date:
#             if not validate(date):
#                 return Response({"result": "Incorrect date format, should be YYYY-MM-DD", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})
#             valid_parameters = {'limit', 'offset', 'date'}
#             provided_parameters = set(request.GET.keys())

#             if not valid_parameters.issuperset(provided_parameters):
#                 return Response({"result": "Invalid query parameters, check spelling for given parameters", 'status': status.HTTP_400_BAD_REQUEST})

#             try:
                
#                 order_details = rbi_odi.objects.filter(date_scraped__startswith=date).values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#                 total_count = rbi_odi.objects.filter(date_scraped__startswith=date).count()
#                 for entry in order_details:
#                     for key, value in entry.items():
#                         if value == "":
#                             entry[key] = "Null"
#                 if len(order_details) > 0:
#                     return Response({"result": order_details,'total_count': total_count,  'status': status.HTTP_200_OK})
#                 else:
#                     return Response({"result": "No Data Provided in your specific date!!!.", 'status': status.HTTP_401_UNAUTHORIZED})
#             except TimeoutError:
#                 return Response({"result": "timeout error", 'status': status.HTTP_502_BAD_GATEWAY})
#             except Exception as err:
#                 return Response({"result": f"An internal server error occurred: {err}", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})
#         else:
#             raise Http404("Page not found")





# class GetOrderdateView(APIView):
#     # permission_classes = (IsAuthenticated,)
    
#     def get(self, request):
#         try:
#             limit = int(request.GET.get('limit', 50))
#             offset = int(request.GET.get('offset', 0))
#         except ValueError:
#             return Response({"result": "Invalid limit or offset value, must be an integer", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})

#         date = str(request.GET.get('date', None))

#         if date:
#             if not validate(date):
#                 return Response({"result": "Incorrect date format, should be YYYY-MM-DD", 'status': status.HTTP_422_UNPROCESSABLE_ENTITY})
#             valid_parameters = {'limit', 'offset', 'date'}
#             provided_parameters = set(request.GET.keys())

#             if not valid_parameters.issuperset(provided_parameters):
#                 return Response({"result": "Invalid query parameters, check spelling for given parameters", 'status': status.HTTP_400_BAD_REQUEST})

#             try:
#                 order_details = rbi_odi.objects.filter(date_scraped__startswith=date).values('SI_NO','Name_of_the_Indian_Party','Name_of_the_JV_WOS','Whether_JV_WOS','Overseas_Country','Major_Activity','FC_Equity','FC_Loan','FC_Guarantee_Issued','FC_Total','Month','Year','date_scraped')[offset:limit]
#                 total_count = rbi_odi.objects.filter(date_scraped__startswith=date).count()
                
#                 # Create a BytesIO object to store zip file contents
#                 zip_buffer = BytesIO()
#                 with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
#                     for entry in order_details:
#                         # Serialize entry to JSON string
#                         entry_json = json.dumps(entry, default=str)
#                         # Add entry as file in the zip archive
#                         zip_file.writestr(f"{entry['SI_NO']}.json", entry_json)
                
#                 # Set the buffer's file pointer to the beginning
#                 zip_buffer.seek(0)
                
#                 # Return the zip file as response
#                 response = HttpResponse(zip_buffer, content_type='application/zip')
#                 response['Content-Disposition'] = 'attachment; filename="order_details.zip"'
#                 return response
            
#             except TimeoutError:
#                 return Response({"result": "timeout error", 'status': status.HTTP_502_BAD_GATEWAY})
#             except Exception as err:
#                 return Response({"result": f"An internal server error occurred: {err}", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})
#         else:
#             raise Http404("Page not found")




