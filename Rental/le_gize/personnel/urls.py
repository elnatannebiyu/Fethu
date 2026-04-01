from django.urls import path
from . import views

app_name = 'personnel'

urlpatterns = [
    path('', views.personnel_list, name='list'),
    path('create/', views.personnel_create, name='create'),
    path('<int:pk>/edit/', views.personnel_edit, name='edit'),
    path('<int:pk>/delete/', views.personnel_delete, name='delete'),
    path('<int:pk>/toggle-active/', views.personnel_toggle_active, name='toggle_active'),
]