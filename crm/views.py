# crm/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

def handler404(request, exception):
    """Кастомная страница 404"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Кастомная страница 500"""
    return render(request, 'errors/500.html', status=500)

from .models import *
from .permissions import *
from .utils import get_user_orders, can_user_access_order, calculate_user_commission
from .forms import *

User = get_user_model()

@login_required
@manager_or_owner_required
def pay_salary(request, salary_id):
    salary = get_object_or_404(SalaryCalculation, id=salary_id, company=request.company, is_paid=False)

    # Отметим как выплаченную
    salary.is_paid = True
    salary.paid_at = timezone.now()
    salary.save()

    # Создаем запись о транзакции
    FinancialTransaction.objects.create(
        company=salary.company,
        user=salary.user,
        transaction_type='salary',
        amount=salary.total_amount,
        description=f"Выплата зарплаты за {salary.period_month}/{salary.period_year}",
        transaction_date=timezone.now()
    )

    messages.success(request, f'Зарплата {salary.user.get_full_name()} выплачена')
    return redirect('my_salary')  # или куда надо


# Авторизация и выбор компании
def login_view(request):
    """Страница входа"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('company_select')
        else:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'auth/login.html')


@login_required
def company_select(request):
    """Выбор компании для работы"""
    user_companies = CompanyUser.objects.filter(
        user=request.user, 
        is_active=True,
        company__is_active=True
    ).select_related('company')
    
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        try:
            company_user = user_companies.get(company_id=company_id)
            request.session['current_company_id'] = company_user.company.id
            return redirect('dashboard')
        except CompanyUser.DoesNotExist:
            messages.error(request, 'Компания не найдена')
    
    return render(request, 'auth/company_select.html', {
        'user_companies': user_companies
    })


def logout_view(request):
    """Выход из системы"""
    logout(request)
    return redirect('login')


# Главная страница (Dashboard)
@company_required
def dashboard(request):
    """Главная страница с основной статистикой"""
    company = request.company
    user_role = request.company_user.role
    
    # Базовая статистика
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Статистика для всех ролей
    stats = {
        'total_clients': company.clients.count(),
        'active_orders': company.orders.filter(status='in_progress').count(),
    }
    
    if user_role in ['owner', 'manager']:
        # Расширенная статистика для владельцев и менеджеров
        stats.update({
            'new_orders': company.orders.filter(status='new').count(),
            'completed_orders_month': company.orders.filter(
                status='completed',
                completion_date__gte=month_start
            ).count(),
            'month_revenue': company.orders.filter(
                status='completed',
                completion_date__gte=month_start
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
            'employees_count': company.company_users.filter(is_active=True).count(),
        })
        
        # Последние заказы
        recent_orders = company.orders.select_related('client').order_by('-created_at')[:10]
    else:
        # Статистика для исполнителей
        user_orders = get_user_orders(request.user, company)
        stats.update({
            'my_active_orders': user_orders.filter(status='in_progress').count(),
            'my_completed_month': user_orders.filter(
                status='completed',
                completion_date__gte=month_start
            ).count(),
        })
        recent_orders = user_orders.select_related('client').order_by('-created_at')[:10]
    
    return render(request, 'crm/dashboard.html', {
        'stats': stats,
        'recent_orders': recent_orders,
    })


# Управление заказами
@company_required
def orders_list(request):
    """Список заказов"""
    company = request.company
    user_role = request.company_user.role
    
    # Получаем заказы в зависимости от роли
    orders = get_user_orders(request.user, company)
    
    # Фильтрация
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    client_filter = request.GET.get('client')
    if client_filter:
        orders = orders.filter(client__name__icontains=client_filter)
    
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(order_date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(order_date__lte=date_to)
    
    # Пагинация
    paginator = Paginator(orders.select_related('client').order_by('-created_at'), 20)
    page = request.GET.get('page')
    orders_page = paginator.get_page(page)
    
    context = {
        'orders': orders_page,
        'status_choices': Order.STATUS_CHOICES,
        'can_create': user_role in ['owner', 'manager'],
    }
    
    return render(request, 'crm/orders/list.html', context)


@manager_or_owner_required
def order_create(request):
    """Создание нового заказа"""
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, company=request.company)
        if form.is_valid():
            order = form.save(commit=False)
            order.company = request.company
            order.created_by = request.user
            order.save()
            
            # Добавляем услуги к заказу
            services_data = request.POST.getlist('services')
            for service_data in services_data:
                # Обработка данных услуг (service_id, quantity, price)
                pass
            
            messages.success(request, 'Заказ успешно создан')
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderCreateForm(company=request.company)
    
    return render(request, 'crm/orders/create.html', {
        'form': form,
        'services': request.company.services.filter(is_active=True),
    })


@company_required
def order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Order, id=order_id, company=request.company)
    
    # Проверяем права доступа
    if not can_user_access_order(request.user, order):
        messages.error(request, 'У вас нет доступа к этому заказу')
        return redirect('orders_list')
    
    return render(request, 'crm/orders/detail.html', {
        'order': order,
        'can_edit': request.company_user.role in ['owner', 'manager'],
    })


# Управление клиентами
@manager_or_owner_required
def clients_list(request):
    """Список клиентов"""
    clients = request.company.clients.all()
    
    # Поиск
    search = request.GET.get('search')
    if search:
        clients = clients.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Фильтр по источнику
    source_filter = request.GET.get('source')
    if source_filter:
        clients = clients.filter(source=source_filter)
    
    paginator = Paginator(clients.order_by('-created_at'), 20)
    page = request.GET.get('page')
    clients_page = paginator.get_page(page)
    
    return render(request, 'crm/clients/list.html', {
        'clients': clients_page,
        'source_choices': Client.SOURCE_CHOICES,
    })


@manager_or_owner_required
def client_create(request):
    """Создание клиента"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.company = request.company
            client.save()
            messages.success(request, 'Клиент успешно создан')
            return redirect('clients_list')
    else:
        form = ClientForm()
    
    return render(request, 'crm/clients/create.html', {'form': form})


# Управление сотрудниками
@owner_required
def employees_list(request):
    """Список сотрудников (только для владельца)"""
    employees = request.company.company_users.filter(is_active=True).select_related('user')
    
    return render(request, 'crm/employees/list.html', {
        'employees': employees,
    })


@owner_required
def employee_create(request):
    """Добавление сотрудника"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            # Создаем или получаем пользователя
            user_data = form.cleaned_data
            # Логика создания пользователя и CompanyUser
            messages.success(request, 'Сотрудник успешно добавлен')
            return redirect('employees_list')
    else:
        form = EmployeeForm()
    
    return render(request, 'crm/employees/create.html', {'form': form})


# Финансы
@company_required
def finances_overview(request):
    """Обзор финансов"""
    company = request.company
    user_role = request.company_user.role
    
    if user_role == 'executor':
        # Исполнители видят только свою зарплату
        return redirect('my_salary')
    
    # Получаем период из GET-параметров
    period = request.GET.get('period', 'current_month')
    today = timezone.now().date()
    
    # Определяем даты в зависимости от периода
    if period == 'current_month':
        date_from = today.replace(day=1)
        date_to = today
    elif period == 'last_month':
        last_month = today.replace(day=1) - timedelta(days=1)
        date_from = last_month.replace(day=1)
        date_to = last_month
    elif period == 'current_quarter':
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        date_from = today.replace(month=quarter_start_month, day=1)
        date_to = today
    elif period == 'current_year':
        date_from = today.replace(month=1, day=1)
        date_to = today
    elif period == 'custom':
        date_from_str = request.GET.get('date_from')
        date_to_str = request.GET.get('date_to')
        
        if date_from_str and date_to_str:
            from datetime import datetime
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        else:
            date_from = today.replace(day=1)
            date_to = today
    else:
        date_from = today.replace(day=1)
        date_to = today
    
    # Доходы и расходы за период
    month_income = company.transactions.filter(
        transaction_type='income',
        transaction_date__date__gte=date_from,
        transaction_date__date__lte=date_to
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    month_expenses = company.transactions.filter(
        transaction_type__in=['expense', 'salary'],
        transaction_date__date__gte=date_from,
        transaction_date__date__lte=date_to
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    balance = month_income - month_expenses
    margin = (balance / month_income * 100) if month_income > 0 else 0
    
    # Структура расходов
    salary_expenses = company.transactions.filter(
        transaction_type='salary',
        transaction_date__date__gte=date_from,
        transaction_date__date__lte=date_to
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    operational_expenses = company.transactions.filter(
        transaction_type='expense',
        transaction_date__date__gte=date_from,
        transaction_date__date__lte=date_to
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    other_expenses = month_expenses - salary_expenses - operational_expenses
    
    # Количество транзакций и средняя сумма
    transactions_count = company.transactions.filter(
        transaction_date__date__gte=date_from,
        transaction_date__date__lte=date_to
    ).count()
    
    average_transaction = ((month_income + month_expenses) / transactions_count) if transactions_count > 0 else 0
    
    # Последние транзакции
    recent_transactions = company.transactions.filter(
        transaction_date__date__gte=date_from,
        transaction_date__date__lte=date_to
    ).order_by('-transaction_date')[:20]
    
    # Данные для графиков (последние 6 месяцев)
    chart_labels = []
    income_data = []
    expense_data = []
    
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_start = month_date.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        chart_labels.append(month_start.strftime('%b'))
        
        month_inc = company.transactions.filter(
            transaction_type='income',
            transaction_date__date__gte=month_start,
            transaction_date__date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_exp = company.transactions.filter(
            transaction_type__in=['expense', 'salary'],
            transaction_date__date__gte=month_start,
            transaction_date__date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        income_data.append(float(month_inc))
        expense_data.append(float(month_exp))
    
    # Финансовые цели (можно вынести в настройки компании)
    income_goal = 500000  # Цель по доходам
    expense_limit = 400000  # Лимит расходов
    
    income_goal_percent = min(100, (month_income / income_goal * 100)) if income_goal > 0 else 0
    expense_control_percent = (month_expenses / expense_limit * 100) if expense_limit > 0 else 0
    
    # Прогноз на конец месяца
    days_passed = (today - date_from).days + 1
    days_in_month = 30  # Упрощенно
    projected_income = (month_income / days_passed) * days_in_month if days_passed > 0 else month_income
    projected_expenses = (month_expenses / days_passed) * days_in_month if days_passed > 0 else month_expenses
    projected_balance = projected_income - projected_expenses
    
    # Изменения по сравнению с предыдущим периодом
    prev_period_start = date_from - timedelta(days=(date_to - date_from).days + 1)
    prev_period_end = date_from - timedelta(days=1)
    
    prev_income = company.transactions.filter(
        transaction_type='income',
        transaction_date__date__gte=prev_period_start,
        transaction_date__date__lte=prev_period_end
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    prev_expenses = company.transactions.filter(
        transaction_type__in=['expense', 'salary'],
        transaction_date__date__gte=prev_period_start,
        transaction_date__date__lte=prev_period_end
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    income_change = ((month_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
    expense_change = ((month_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0
    
    context = {
        'month_income': month_income,
        'month_expenses': month_expenses,
        'balance': balance,
        'margin': margin,
        'salary_expenses': salary_expenses,
        'operational_expenses': operational_expenses,
        'other_expenses': other_expenses,
        'transactions_count': transactions_count,
        'average_transaction': average_transaction,
        'recent_transactions': recent_transactions,
        'chart_labels': chart_labels,
        'income_data': income_data,
        'expense_data': expense_data,
        'income_goal': income_goal,
        'expense_limit': expense_limit,
        'income_goal_percent': income_goal_percent,
        'expense_control_percent': expense_control_percent,
        'projected_balance': projected_balance,
        'income_change': income_change,
        'expense_change': expense_change,
    }
    
    return render(request, 'crm/finances/overview.html', context)


@company_required
def my_salary(request):
    """Моя зарплата (для всех ролей)"""
    user = request.user
    company = request.company
    
    # Получаем расчеты зарплаты пользователя
    salary_calculations = SalaryCalculation.objects.filter(
        company=company,
        user=user
    ).order_by('-period_year', '-period_month')
    
    # Текущий месяц
    current_date = timezone.now().date()
    current_commission = calculate_user_commission(
        user, company, current_date.year, current_date.month
    )
    
    # Дополнительные данные для шаблона
    company_user = request.company_user
    current_total = company_user.salary_rate + current_commission
    
    # Прогресс месяца (для расчета "осталось дней")
    month_start = current_date.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_in_month = (next_month - month_start).days
    days_passed = (current_date - month_start).days + 1
    month_progress = (days_passed / days_in_month) * 100
    days_left = days_in_month - days_passed
    
    # Статистика текущего месяца
    current_completed_orders = Order.objects.filter(
        company=company,
        executors__user=user,
        status='completed',
        completion_date__year=current_date.year,
        completion_date__month=current_date.month
    ).count()
    
    context = {
        'salary_calculations': salary_calculations,
        'current_commission': current_commission,
        'company_user': company_user,
        'current_total': current_total,
        'month_progress': month_progress,
        'days_left': days_left,
        'current_completed_orders': current_completed_orders,
        'current_bonuses': 0,  # Можно добавить логику бонусов
        'current_penalties': 0,  # Можно добавить логику штрафов
    }
    
    # ИСПРАВЛЕНИЕ: изменить путь с 'crm/finances/my_salary.html' на 'crm/finances/my_salary.html'
    return render(request, 'crm/finances/my_salary.html', context)


# API endpoints для AJAX
@company_required
def api_services(request):
    """API для получения услуг компании"""
    services = request.company.services.filter(is_active=True).values(
        'id', 'name', 'base_price', 'unit'
    )
    return JsonResponse(list(services), safe=False)


@company_required
def api_clients(request):
    """API для поиска клиентов"""
    query = request.GET.get('q', '')
    clients = request.company.clients.filter(
        name__icontains=query
    ).values('id', 'name', 'phone')[:10]
    return JsonResponse(list(clients), safe=False)


@manager_or_owner_required
def order_edit(request, order_id):
    """Редактирование заказа"""
    order = get_object_or_404(Order, id=order_id, company=request.company)
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, instance=order, company=request.company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заказ успешно обновлен')
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderCreateForm(instance=order, company=request.company)
    
    return render(request, 'crm/orders/edit.html', {
        'form': form,
        'order': order,
        'services': request.company.services.filter(is_active=True),
    })


@company_required
def client_detail(request, client_id):
    """Детали клиента"""
    client = get_object_or_404(Client, id=client_id, company=request.company)
    
    # Получаем заказы клиента
    client_orders = client.orders.all().order_by('-created_at')
    
    return render(request, 'crm/clients/detail.html', {
        'client': client,
        'orders': client_orders,
        'can_edit': request.company_user.role in ['owner', 'manager'],
    })


@manager_or_owner_required
def client_edit(request, client_id):
    """Редактирование клиента"""
    client = get_object_or_404(Client, id=client_id, company=request.company)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент успешно обновлен')
            return redirect('client_detail', client_id=client.id)
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'crm/clients/edit.html', {
        'form': form,
        'client': client,
    })


@manager_or_owner_required
def services_list(request):
    """Список услуг"""
    services = request.company.services.all().order_by('name')
    
    return render(request, 'crm/services/list.html', {
        'services': services,
    })


@manager_or_owner_required
def service_create(request):
    """Создание услуги"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.company = request.company
            service.save()
            messages.success(request, 'Услуга успешно создана')
            return redirect('services_list')
    else:
        form = ServiceForm()
    
    return render(request, 'crm/services/create.html', {'form': form})


@manager_or_owner_required
def service_edit(request, service_id):
    """Редактирование услуги"""
    service = get_object_or_404(Service, id=service_id, company=request.company)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Услуга успешно обновлена')
            return redirect('services_list')
    else:
        form = ServiceForm(instance=service)
    
    return render(request, 'crm/services/edit.html', {
        'form': form,
        'service': service,
    })


@owner_required
def employee_detail(request, employee_id):
    """Детали сотрудника"""
    employee = get_object_or_404(
        CompanyUser, 
        id=employee_id, 
        company=request.company
    )
    
    # Статистика сотрудника
    current_month = timezone.now().date().replace(day=1)
    month_orders = Order.objects.filter(
        company=request.company,
        executors__user=employee.user,
        created_at__gte=current_month
    ).count()
    
    return render(request, 'crm/employees/detail.html', {
        'employee': employee,
        'month_orders': month_orders,
    })


@owner_required
def employee_edit(request, employee_id):
    """Редактирование сотрудника"""
    employee = get_object_or_404(
        CompanyUser, 
        id=employee_id, 
        company=request.company
    )
    
    if request.method == 'POST':
        # Простая форма для редактирования CompanyUser
        role = request.POST.get('role')
        salary_rate = request.POST.get('salary_rate', 0)
        commission_rate = request.POST.get('commission_rate', 0)
        
        if role in dict(CompanyUser.ROLE_CHOICES):
            employee.role = role
            employee.salary_rate = salary_rate
            employee.commission_rate = commission_rate
            employee.save()
            
            messages.success(request, 'Данные сотрудника обновлены')
            return redirect('employee_detail', employee_id=employee.id)
    
    return render(request, 'crm/employees/edit.html', {
        'employee': employee,
        'role_choices': CompanyUser.ROLE_CHOICES,
    })


@manager_or_owner_required
def salary_calculate(request):
    """Расчет зарплаты"""
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
            
            messages.success(request, 'Зарплата рассчитана')
            return redirect('finances_overview')
    else:
        form = SalaryCalculationForm(company=request.company)
    
    return render(request, 'crm/salary/calculate.html', {'form': form})


@manager_or_owner_required
def transactions_list(request):
    """Список финансовых операций"""
    transactions = request.company.transactions.all().order_by('-transaction_date')
    
    # Фильтрация
    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Пагинация
    paginator = Paginator(transactions, 20)
    page = request.GET.get('page')
    transactions_page = paginator.get_page(page)
    
    return render(request, 'crm/finances/transactions.html', {
        'transactions': transactions_page,
        'transaction_types': FinancialTransaction.TRANSACTION_TYPES,
    })


@manager_or_owner_required
def transaction_add(request):
    """Добавление финансовой операции"""
    if request.method == 'POST':
        form = FinancialTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.company = request.company
            transaction.save()
            messages.success(request, 'Операция добавлена')
            return redirect('transactions_list')
    else:
        form = FinancialTransactionForm()
    
    return render(request, 'crm/finances/add_transaction.html', {'form': form})


@owner_required
def company_settings(request):
    """Настройки компании"""
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=request.company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки компании обновлены')
            return redirect('company_settings')
    else:
        form = CompanyForm(instance=request.company)
    
    return render(request, 'crm/company/settings.html', {'form': form})


# Дополнительные API endpoints
@company_required  
def api_order_status_update(request, order_id):
    """API для обновления статуса заказа"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, company=request.company)
        
        # Проверяем права
        if not can_user_access_order(request.user, order):
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            if new_status == 'completed':
                order.completion_date = timezone.now()
            order.save()
            
            return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Ошибка обновления'}, status=400)


@company_required
def api_order_executors(request, order_id):
    """API для получения исполнителей заказа"""
    order = get_object_or_404(Order, id=order_id, company=request.company)
    
    if not can_user_access_order(request.user, order):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    
    executors = order.executors.select_related('user').values(
        'user__first_name', 'user__last_name', 'work_hours', 'status'
    )
    
    return JsonResponse(list(executors), safe=False)


@company_required
def api_salary_calculate(request):
    """API для расчета зарплаты"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        year = int(request.POST.get('year'))
        month = int(request.POST.get('month'))
        
        try:
            user = User.objects.get(id=user_id)
            commission = calculate_user_commission(user, request.company, year, month)
            
            return JsonResponse({
                'commission': float(commission),
                'success': True
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
    
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


@company_required
def api_dashboard_stats(request):
    """API для статистики дашборда"""
    company = request.company
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    stats = {
        'total_clients': company.clients.count(),
        'active_orders': company.orders.filter(status='in_progress').count(),
        'new_orders': company.orders.filter(status='new').count(),
        'month_revenue': float(
            company.orders.filter(
                status='completed',
                completion_date__gte=month_start
            ).aggregate(total=Sum('total_amount'))['total'] or 0
        )
    }
    
    return JsonResponse(stats)