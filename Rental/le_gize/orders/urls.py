from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order pages
    path('', views.order_page, name='order_page'),
    path('list/', views.order_list, name='list'),
    path('<int:order_id>/', views.order_detail, name='detail'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel'),
    
    # Return page
    path('return/', views.return_page, name='return_page'),
    
    # Loading personnel views
    path('assigned/', views.assigned_orders, name='assigned_orders'),
    path('confirm-loading/<int:allocation_id>/', views.confirm_loading, name='confirm_loading'),  # Fixed: removed 'api/' prefix and _api suffix
    
    # API endpoints for order creation
    path('api/get-product-extras/', views.get_product_extras, name='get_product_extras'),
    path('api/check-availability/', views.check_availability_api, name='check_availability'),
    path('api/calculate-order-total/', views.calculate_order_total, name='calculate_order_total'),
    path('api/initiate-order/', views.initiate_order_api, name='initiate_order'),
    
    # API endpoints for returns
    path('api/search-active-orders/', views.search_active_orders_api, name='search_active_orders'),
    path('api/get-order-details/<int:order_id>/', views.get_order_details_api, name='get_order_details'),
    path('api/finalize-return/', views.finalize_return_api, name='finalize_return'),
]