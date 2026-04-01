from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard, name='dashboard'),
    path('orders/', views.orders_report, name='orders_report'),
    path('orders/csv/', views.orders_report_csv, name='orders_csv'),
    path('products/', views.products_report, name='products_report'),
    path('products/csv/', views.products_report_csv, name='products_csv'),
    path('personnel/', views.personnel_report, name='personnel_report'),
    path('personnel/csv/', views.personnel_report_csv, name='personnel_csv'),
    path('financial/', views.financial_report, name='financial_report'),
]