from django.urls import path
from  .views import *

urlpatterns = [
    
    path('<str:type_of_order>/getMcaOrderByYear/', GetOrderYearView.as_view(), name='getMcaOrderByYear'),  
    path('<str:type_of_order>/download_all_pdfs/', DownloadAllPDFsView.as_view(), name='download_all_pdfs'),
    
    path('<str:type_of_order>/getMcaOrderByDate/', GetOrderDateView.as_view(), name='getMcaOrderByDate'),  
    path('<str:type_of_order>/download_pdfs/', DownloadPDFsView.as_view(), name='download_pdfs'),
    
    
    path('<path:invalid_path>', Custom404View.as_view(), name='invalid_path'),
    # path('<str:whether>/getSebiOrderByDate/<int:year>/<int:month>/', GetOrderdateView.as_view(), name='getSebiOrderByDate'),
    # path('<str:whether>/getSebiOrderByDate/<int:year>/<int:month>/<int:day>/',GetOrderdateView.as_view(), name='getSebiOrderByDate'),
    
    path('login/', Login.as_view(), name='login'),
    path('logout/', Logout.as_view(), name='logout'),
    
    path('<str:whether>/download_zip/', DownloadZipView.as_view(), name='download_zip'),
    # path('getOdiOrderByDate/',GetOrderdateView.as_view(), name='GetOrderdateView'),
    path('zipdownload/',zipdownload.as_view(), name='zipdownload'),
    # path('downloadzip1/',downloadzip1.as_view(), name='downloadzip1'),
    # path('download_zip/', DownloadZipView.as_view(), name='download_zip'),
    # path('getOrdermonthView/',GetOrdermonthView.as_view(), name='GetOrdermonthView'),
    # path('getOrdertotalview/',GetOrdertotalview.as_view(), name='GetOrdertotalview'),
    
 
]




