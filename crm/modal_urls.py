# crm/modal_urls.py
from django.urls import path
from . import modal_views

urlpatterns = [
    # === МОДАЛЬНЫЕ ОКНА ДЛЯ ЗАКАЗОВ ===
    path('modals/orders/<int:order_id>/detail/', modal_views.order_detail_modal, name='order_detail_modal'),
    path('modals/orders/create/', modal_views.order_create_modal, name='order_create_modal'),
    path('modals/orders/<int:order_id>/edit/', modal_views.order_edit_modal, name='order_edit_modal'),
    path('modals/orders/<int:order_id>/assign-executor/', modal_views.assign_executor_modal, name='assign_executor_modal'),
    
    # === МОДАЛЬНЫЕ ОКНА ДЛЯ КЛИЕНТОВ ===
    path('modals/clients/create/', modal_views.client_create_modal, name='client_create_modal'),
    path('modals/clients/<int:client_id>/edit/', modal_views.client_edit_modal, name='client_edit_modal'),
    path('modals/clients/<int:client_id>/detail/', modal_views.client_detail_modal, name='client_detail_modal'),
    
    # === МОДАЛЬНЫЕ ОКНА ДЛЯ УСЛУГ ===
    path('modals/services/create/', modal_views.service_create_modal, name='service_create_modal'),
    path('modals/services/<int:service_id>/edit/', modal_views.service_edit_modal, name='service_edit_modal'),
    
    # === МОДАЛЬНЫЕ ОКНА ДЛЯ СОТРУДНИКОВ ===
    path('modals/employees/create/', modal_views.employee_create_modal, name='employee_create_modal'),
    path('modals/employees/<int:employee_id>/detail/', modal_views.employee_detail_modal, name='employee_detail_modal'),
    
    # === МОДАЛЬНЫЕ ОКНА ДЛЯ ФИНАНСОВ ===
    path('modals/transactions/create/', modal_views.transaction_create_modal, name='transaction_create_modal'),
    path('modals/salary/calculate/', modal_views.salary_calculate_modal, name='salary_calculate_modal'),
    
    # === МОДАЛЬНЫЕ ОКНА ДЛЯ ОТЧЕТОВ ===
    path('modals/reports/orders/', modal_views.orders_report_modal, name='orders_report_modal'),
    path('modals/my-performance/', modal_views.my_performance_modal, name='my_performance_modal'),
    
    # === БЫСТРЫЕ ДЕЙСТВИЯ ===
    path('quick/orders/<int:order_id>/status/', modal_views.quick_status_update, name='quick_status_update'),
    path('quick/orders/<int:order_id>/assign/', modal_views.quick_assign_executor, name='quick_assign_executor'),
]
