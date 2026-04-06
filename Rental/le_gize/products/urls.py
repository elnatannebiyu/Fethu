from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product URLs
    path('', views.product_list, name='list'),
    path('<int:pk>/', views.product_detail, name='detail'),
    path('create/', views.product_create, name='create'),
    path('<int:pk>/edit/', views.product_edit, name='edit'),
    path('<int:pk>/delete/', views.product_delete, name='delete'),
    path('<int:pk>/toggle-active/', views.product_toggle_active, name='toggle_active'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Extra URLs
    path('extras/', views.extra_list, name='extra_list'),
    path('extras/create/', views.extra_create, name='extra_create'),
    path('extras/<int:pk>/edit/', views.extra_edit, name='extra_edit'),
    path('extras/<int:pk>/delete/', views.extra_delete, name='extra_delete'),
]