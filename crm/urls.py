from django.urls import path
from . import views

urlpatterns = [
    # Авторизация
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('company/select/', views.company_select, name='company_select'),
    
    # Главная страница
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Заказы
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    
    # Клиенты
    path('clients/', views.clients_list, name='clients_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', views.client_edit, name='client_edit'),
    
    # Услуги
    path('services/', views.services_list, name='services_list'),
    path('services/create/', views.service_create, name='service_create'),
    path('services/<int:service_id>/edit/', views.service_edit, name='service_edit'),
    
    # Сотрудники
    path('employees/', views.employees_list, name='employees_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:employee_id>/edit/', views.employee_edit, name='employee_edit'),
    
    # Финансы
    path('finances/', views.finances_overview, name='finances_overview'),
    path('finances/salary/', views.my_salary, name='my_salary'),
    path('finances/salary/calculate/', views.salary_calculate, name='salary_calculate'),
    path('finances/transactions/', views.transactions_list, name='transactions_list'),
    path('finances/transactions/add/', views.transaction_add, name='transaction_add'),
    
    # Компания
    path('company/settings/', views.company_settings, name='company_settings'),
]