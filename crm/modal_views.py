# crm/modal_views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime, timedelta
import json

from .models import *
from .permissions import *
from .utils import get_user_orders, can_user_access_order, calculate_user_commission
from .forms import *


# Базовый декоратор для модальных окон
def modal_view(template_name):
    """Декоратор для модальных представлений"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Выполняем основную логику представления
            context = view_func(request, *args, **kwargs)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX запрос - возвращаем только HTML контент
                if isinstance(context, dict):
                    html = render_to_string(template_name, context, request=request)
                    return JsonResponse({
                        'html': html,
                        'success': True
                    })
                else:
                    return context  # Уже готовый JsonResponse
            else:
                # Обычный запрос - возвращаем полную страницу
                return render(request, template_name, context)
        return wrapper
    return decorator


# === МОДАЛЬНЫЕ ОКНА ДЛЯ ЗАКАЗОВ ===

@company_required
@modal_view('crm/modals/order_detail_modal.html')
def order_detail_modal(request, order_id):
    """Модальное окно с детальной информацией о заказе"""
    order = get_object_or_404(Order, id=order_id, company=request.company)
    
    # Проверяем права доступа
    if not can_user_access_order(request.user, order):
        return JsonResponse({'error': 'У вас нет доступа к этому заказу'}, status=403)
    
    # Получаем связанные данные
    order_services = order.order_services.select_related('service').all()
    order_executors = order.executors.select_related('user').all()
    
    # Статистика заказа
    total_work_hours = order_executors.aggregate(
        total_hours=Sum('work_hours')
    )['total_hours'] or 0
    
    total_commission = order_executors.aggregate(
        total_commission=Sum('commission_amount')
    )['total_commission'] or 0
    
    return {
        'order': order,
        'order_services': order_services,
        'order_executors': order_executors,
        'total_work_hours': total_work_hours,
        'total_commission': total_commission,
        'can_edit': request.company_user.role in ['owner', 'manager'],
        'can_change_status': can_user_access_order(request.user, order),
        'status_choices': Order.STATUS_CHOICES,
    }


@manager_or_owner_required
@modal_view('crm/modals/order_create_modal.html')
def order_create_modal(request):
    """Модальное окно создания заказа"""
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, company=request.company)
        if form.is_valid():
            order = form.save(commit=False)
            order.company = request.company
            order.created_by = request.user
            order.save()
            
            # Обработка услуг из POST данных
            services_data = json.loads(request.POST.get('services_data', '[]'))
            total_amount = 0
            
            for service_data in services_data:
                service = get_object_or_404(Service, id=service_data['service_id'], company=request.company)
                order_service = OrderService.objects.create(
                    order=order,
                    service=service,
                    quantity=service_data['quantity'],
                    unit_price=service_data['unit_price'],
                )
                total_amount += order_service.total_price
            
            order.total_amount = total_amount
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Заказ успешно создан',
                'order_id': order.id,
                'redirect_url': f'/orders/{order.id}/'
            })
    else:
        form = OrderCreateForm(company=request.company)
    
    return {
        'form': form,
        'clients': request.company.clients.all(),
        'services': request.company.services.filter(is_active=True),
    }


@manager_or_owner_required
@modal_view('crm/modals/order_edit_modal.html')
def order_edit_modal(request, order_id):
    """Модальное окно редактирования заказа"""
    order = get_object_or_404(Order, id=order_id, company=request.company)
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, instance=order, company=request.company)
        if form.is_valid():
            order = form.save()
            
            # Обновляем услуги
            order.order_services.all().delete()  # Удаляем старые
            services_data = json.loads(request.POST.get('services_data', '[]'))
            total_amount = 0
            
            for service_data in services_data:
                service = get_object_or_404(Service, id=service_data['service_id'], company=request.company)
                order_service = OrderService.objects.create(
                    order=order,
                    service=service,
                    quantity=service_data['quantity'],
                    unit_price=service_data['unit_price'],
                )
                total_amount += order_service.total_price
            
            order.total_amount = total_amount
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Заказ успешно обновлен',
                'order_id': order.id
            })
    else:
        form = OrderCreateForm(instance=order, company=request.company)
    
    return {
        'form': form,
        'order': order,
        'clients': request.company.clients.all(),
        'services': request.company.services.filter(is_active=True),
        'current_services': order.order_services.select_related('service').all(),
    }


@manager_or_owner_required
@modal_view('crm/modals/assign_executor_modal.html')
def assign_executor_modal(request, order_id):
    """Модальное окно назначения исполнителя"""
    order = get_object_or_404(Order, id=order_id, company=request.company)
    
    if request.method == 'POST':
        executor_id = request.POST.get('executor_id')
        work_hours = request.POST.get('work_hours', 0)
        commission_rate = request.POST.get('commission_rate', 0)
        
        try:
            executor = User.objects.get(id=executor_id)
            # Проверяем, что пользователь принадлежит к компании
            CompanyUser.objects.get(
                user=executor, 
                company=request.company, 
                is_active=True
            )
            
            # Проверяем, не назначен ли уже
            if not order.executors.filter(user=executor).exists():
                commission_amount = (order.total_amount * float(commission_rate)) / 100
                
                OrderExecutor.objects.create(
                    order=order,
                    user=executor,
                    work_hours=work_hours,
                    commission_amount=commission_amount,
                    status='assigned'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Исполнитель {executor.get_full_name()} назначен'
                })
            else:
                return JsonResponse({
                    'error': 'Исполнитель уже назначен на этот заказ'
                }, status=400)
                
        except (User.DoesNotExist, CompanyUser.DoesNotExist):
            return JsonResponse({
                'error': 'Исполнитель не найден'
            }, status=404)
    
    # Получаем доступных исполнителей
    executors = CompanyUser.objects.filter(
        company=request.company,
        role='executor',
        is_active=True
    ).select_related('user')
    
    # Исключаем уже назначенных
    assigned_executor_ids = order.executors.values_list('user_id', flat=True)
    available_executors = executors.exclude(user_id__in=assigned_executor_ids)
    
    return {
        'order': order,
        'executors': available_executors,
    }


# === МОДАЛЬНЫЕ ОКНА ДЛЯ КЛИЕНТОВ ===

@manager_or_owner_required
@modal_view('crm/modals/client_create_modal.html')
def client_create_modal(request):
    """Модальное окно создания клиента"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.company = request.company
            client.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Клиент успешно создан',
                'client_id': client.id,
                'client_name': client.name
            })
    else:
        form = ClientForm()
    
    return {'form': form}


@manager_or_owner_required
@modal_view('crm/modals/client_edit_modal.html')
def client_edit_modal(request, client_id):
    """Модальное окно редактирования клиента"""
    client = get_object_or_404(Client, id=client_id, company=request.company)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Клиент успешно обновлен'
            })
    else:
        form = ClientForm(instance=client)
    
    return {
        'form': form,
        'client': client,
    }


@company_required
@modal_view('crm/modals/client_detail_modal.html')
def client_detail_modal(request, client_id):
    """Модальное окно с деталями клиента"""
    client = get_object_or_404(Client, id=client_id, company=request.company)
    
    # Получаем заказы клиента
    client_orders = client.orders.all().order_by('-created_at')
    
    # Статистика клиента
    total_orders = client_orders.count()
    completed_orders = client_orders.filter(status='completed').count()
    total_spent = client_orders.filter(status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Последние заказы (ограничиваем для модального окна)
    recent_orders = client_orders[:5]
    
    return {
        'client': client,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_spent': total_spent,
        'success_rate': (completed_orders / total_orders * 100) if total_orders > 0 else 0,
        'can_edit': request.company_user.role in ['owner', 'manager'],
    }


# === МОДАЛЬНЫЕ ОКНА ДЛЯ УСЛУГ ===

@manager_or_owner_required
@modal_view('crm/modals/service_create_modal.html')
def service_create_modal(request):
    """Модальное окно создания услуги"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.company = request.company
            service.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Услуга успешно создана',
                'service_id': service.id,
                'service_name': service.name
            })
    else:
        form = ServiceForm()
    
    return {'form': form}


@manager_or_owner_required
@modal_view('crm/modals/service_edit_modal.html')
def service_edit_modal(request, service_id):
    """Модальное окно редактирования услуги"""
    service = get_object_or_404(Service, id=service_id, company=request.company)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Услуга успешно обновлена'
            })
    else:
        form = ServiceForm(instance=service)
    
    return {
        'form': form,
        'service': service,
    }


# === МОДАЛЬНЫЕ ОКНА ДЛЯ СОТРУДНИКОВ ===

@owner_required
@modal_view('crm/modals/employee_create_modal.html')
def employee_create_modal(request):
    """Модальное окно добавления сотрудника"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Определяем пользователя
            if data['existing_user']:
                user = data['existing_user']
            else:
                # Создаем нового пользователя
                user = User.objects.create_user(
                    username=data['username'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    email=data['email'],
                    password=data['password']
                )
            
            # Создаем связь с компанией
            CompanyUser.objects.create(
                company=request.company,
                user=user,
                role=data['role'],
                salary_rate=data['salary_rate'],
                commission_rate=data['commission_rate']
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Сотрудник успешно добавлен'
            })
    else:
        form = EmployeeForm()
    
    return {'form': form}


@owner_required
@modal_view('crm/modals/employee_detail_modal.html')
def employee_detail_modal(request, employee_id):
    """Модальное окно с деталями сотрудника"""
    employee = get_object_or_404(
        CompanyUser, 
        id=employee_id, 
        company=request.company
    )
    
    # Статистика сотрудника за текущий месяц
    current_month = timezone.now().date().replace(day=1)
    
    # Заказы исполнителя
    if employee.role == 'executor':
        month_orders = Order.objects.filter(
            company=request.company,
            executors__user=employee.user,
            created_at__gte=current_month
        ).count()
        
        completed_orders = Order.objects.filter(
            company=request.company,
            executors__user=employee.user,
            status='completed',
            completion_date__gte=current_month
        ).count()
        
        total_commission = calculate_user_commission(
            employee.user, 
            request.company, 
            current_month.year, 
            current_month.month
        )
    else:
        month_orders = 0
        completed_orders = 0
        total_commission = 0
    
    # Последние зарплаты
    recent_salaries = SalaryCalculation.objects.filter(
        company=request.company,
        user=employee.user
    ).order_by('-period_year', '-period_month')[:3]
    
    return {
        'employee': employee,
        'month_orders': month_orders,
        'completed_orders': completed_orders,
        'total_commission': total_commission,
        'recent_salaries': recent_salaries,
    }


# === МОДАЛЬНЫЕ ОКНА ДЛЯ ФИНАНСОВ ===

@manager_or_owner_required
@modal_view('crm/modals/transaction_create_modal.html')
def transaction_create_modal(request):
    """Модальное окно добавления финансовой операции"""
    if request.method == 'POST':
        form = FinancialTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.company = request.company
            transaction.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Операция успешно добавлена'
            })
    else:
        form = FinancialTransactionForm()
    
    return {'form': form}


@manager_or_owner_required
@modal_view('crm/modals/salary_calculate_modal.html')
def salary_calculate_modal(request):
    """Модальное окно расчета зарплаты"""
    if request.method == 'POST':
        form = SalaryCalculationForm(request.POST, company=request.company)
        if form.is_valid():
            salary_calc = form.save(commit=False)
            salary_calc.company = request.company
            
            # Автоматически рассчитываем комиссию
            commission = calculate_user_commission(
                salary_calc.user,
                request.company,
                salary_calc.period_year,
                salary_calc.period_month
            )
            salary_calc.commission_total = commission
            salary_calc.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Зарплата рассчитана',
                'total_amount': float(salary_calc.total_amount)
            })
    else:
        form = SalaryCalculationForm(company=request.company)
    
    return {'form': form}


# === МОДАЛЬНЫЕ ОКНА ДЛЯ ОТЧЕТОВ ===

@manager_or_owner_required
@modal_view('crm/modals/orders_report_modal.html')
def orders_report_modal(request):
    """Модальное окно отчета по заказам"""
    # Получаем параметры из GET
    period = request.GET.get('period', 'current_month')
    status_filter = request.GET.get('status', 'all')
    
    # Определяем период
    today = timezone.now().date()
    if period == 'current_month':
        date_from = today.replace(day=1)
        date_to = today
    elif period == 'last_month':
        last_month = today.replace(day=1) - timedelta(days=1)
        date_from = last_month.replace(day=1)
        date_to = last_month
    elif period == 'current_year':
        date_from = today.replace(month=1, day=1)
        date_to = today
    else:
        date_from = today.replace(day=1)
        date_to = today
    
    # Базовый запрос
    orders = Order.objects.filter(
        company=request.company,
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    # Фильтр по статусу
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Статистика
    stats = {
        'total_orders': orders.count(),
        'total_amount': orders.aggregate(Sum('total_amount'))['total_amount'] or 0,
        'by_status': {},
    }
    
    # Группировка по статусам
    for status_code, status_name in Order.STATUS_CHOICES:
        count = orders.filter(status=status_code).count()
        amount = orders.filter(status=status_code).aggregate(
            Sum('total_amount')
        )['total_amount'] or 0
        
        stats['by_status'][status_code] = {
            'name': status_name,
            'count': count,
            'amount': amount
        }
    
    return {
        'stats': stats,
        'period': period,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Order.STATUS_CHOICES,
    }


@company_required
@modal_view('crm/modals/my_performance_modal.html')
def my_performance_modal(request):
    """Модальное окно с производительностью сотрудника"""
    user = request.user
    company = request.company
    
    # Период - текущий месяц
    current_month = timezone.now().date().replace(day=1)
    
    # Мои заказы за месяц
    my_orders = get_user_orders(user, company).filter(
        created_at__gte=current_month
    )
    
    # Статистика
    stats = {
        'total_orders': my_orders.count(),
        'completed_orders': my_orders.filter(status='completed').count(),
        'in_progress_orders': my_orders.filter(status='in_progress').count(),
        'total_hours': my_orders.aggregate(
            Sum('executors__work_hours')
        )['executors__work_hours__sum'] or 0,
        'total_commission': calculate_user_commission(
            user, company, current_month.year, current_month.month
        ),
    }
    
    # Процент выполнения
    if stats['total_orders'] > 0:
        stats['completion_rate'] = (stats['completed_orders'] / stats['total_orders']) * 100
    else:
        stats['completion_rate'] = 0
    
    # Последние заказы
    recent_orders = my_orders.select_related('client').order_by('-created_at')[:5]
    
    return {
        'stats': stats,
        'recent_orders': recent_orders,
        'company_user': request.company_user,
    }


# === БЫСТРЫЕ ДЕЙСТВИЯ ===

@company_required
def quick_status_update(request, order_id):
    """Быстрое обновление статуса заказа"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, company=request.company)
        
        if not can_user_access_order(request.user, order):
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            
            if new_status == 'completed' and old_status != 'completed':
                order.completion_date = timezone.now()
            elif new_status != 'completed':
                order.completion_date = None
                
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Статус изменен на "{order.get_status_display()}"',
                'new_status': new_status,
                'new_status_display': order.get_status_display()
            })
    
    return JsonResponse({'error': 'Ошибка обновления'}, status=400)


@manager_or_owner_required
def quick_assign_executor(request, order_id):
    """Быстрое назначение исполнителя"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, company=request.company)
        executor_id = request.POST.get('executor_id')
        
        try:
            executor = User.objects.get(id=executor_id)
            company_user = CompanyUser.objects.get(
                user=executor,
                company=request.company,
                role='executor',
                is_active=True
            )
            
            if not order.executors.filter(user=executor).exists():
                OrderExecutor.objects.create(
                    order=order,
                    user=executor,
                    commission_amount=(order.total_amount * company_user.commission_rate) / 100
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Назначен исполнитель: {executor.get_full_name()}'
                })
            else:
                return JsonResponse({
                    'error': 'Исполнитель уже назначен'
                }, status=400)
                
        except (User.DoesNotExist, CompanyUser.DoesNotExist):
            return JsonResponse({
                'error': 'Исполнитель не найден'
            }, status=404)
    
    return JsonResponse({'error': 'Ошибка назначения'}, status=400)