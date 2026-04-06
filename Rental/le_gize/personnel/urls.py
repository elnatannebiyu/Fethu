from django.urls import path
from . import views

app_name = 'personnel'

urlpatterns = [
    # Loading Personnel URLs
    path('', views.personnel_list, name='list'),
    path('create/', views.personnel_create, name='create'),
    path('<int:pk>/edit/', views.personnel_edit, name='edit'),
    path('<int:pk>/delete/', views.personnel_delete, name='delete'),
    path('<int:pk>/toggle-active/', views.personnel_toggle_active, name='toggle_active'),
    path('my-assignments/', views.my_assignments, name='my_assignments'),
    path('confirm-assignment/<int:allocation_id>/', views.confirm_assignment, name='confirm_assignment'),
    
    # Reception URLs
    path('reception/dashboard/', views.reception_dashboard, name='reception_dashboard'),
    path('reception/my-dashboard/', views.reception_user_dashboard, name='reception_user_dashboard'),
    path('reception/', views.reception_list, name='reception_list'),
    path('reception/create/', views.reception_create, name='reception_create'),
    path('reception/<int:pk>/edit/', views.reception_edit, name='reception_edit'),
    path('reception/<int:pk>/delete/', views.reception_delete, name='reception_delete'),
    path('reception/<int:pk>/toggle-active/', views.reception_toggle_active, name='reception_toggle_active'),
]