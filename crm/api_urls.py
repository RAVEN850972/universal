from django.urls import path
from . import views

urlpatterns = [
    # API для AJAX запросов
    path('services/', views.api_services, name='api_services'),
    path('clients/', views.api_clients, name='api_clients'),
    path('orders/<int:order_id>/status/', views.api_order_status_update, name='api_order_status_update'),
    path('orders/<int:order_id>/executors/', views.api_order_executors, name='api_order_executors'),
    path('salary/calculate/', views.api_salary_calculate, name='api_salary_calculate'),
    path('dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
]