from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('loading-dashboard/', views.loading_dashboard, name='loading_dashboard'),
    path('reception-dashboard/', views.reception_dashboard, name='reception_dashboard'),
]