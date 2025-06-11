# crm/middleware.py
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from .models import Company, CompanyUser


class CompanyMiddleware:
    """Мидлвара для обработки мультитенантности"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем admin, auth, static и API endpoints
        excluded_paths = [
            '/admin/', 
            '/auth/', 
            '/api/auth/',
            '/static/',
            '/media/',
            '/favicon.ico'
        ]
        
        # Проверяем исключенные пути
        for path in excluded_paths:
            if request.path.startswith(path):
                response = self.get_response(request)
                return response

        # Если пользователь не авторизован, пропускаем мидлвару
        if not request.user.is_authenticated:
            response = self.get_response(request)
            return response

        # Если мы на странице выбора компании, не проверяем компанию
        if request.path == reverse('company_select'):
            response = self.get_response(request)
            return response

        # Если пользователь авторизован, получаем его компанию
        company_id = request.session.get('current_company_id')
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id, is_active=True)
                company_user = CompanyUser.objects.get(
                    company=company, 
                    user=request.user, 
                    is_active=True
                )
                request.company = company
                request.company_user = company_user
            except (Company.DoesNotExist, CompanyUser.DoesNotExist):
                # Компания не найдена или пользователь не принадлежит к ней
                if 'current_company_id' in request.session:
                    del request.session['current_company_id']
                return redirect('company_select')
        else:
            # Если компания не выбрана, перенаправляем на выбор компании
            return redirect('company_select')

        response = self.get_response(request)
        return response


# crm/permissions.py
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from functools import wraps
from .models import CompanyUser


def company_required(view_func):
    """Декоратор для проверки принадлежности к компании"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'company') or not hasattr(request, 'company_user'):
            raise PermissionDenied("Доступ запрещен: не выбрана компания")
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(required_roles):
    """Декоратор для проверки роли пользователя"""
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    def decorator(view_func):
        @wraps(view_func)
        @company_required
        def wrapper(request, *args, **kwargs):
            if request.company_user.role not in required_roles:
                raise PermissionDenied(
                    f"Доступ запрещен: требуется роль {', '.join(required_roles)}"
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def owner_required(view_func):
    """Декоратор для проверки прав владельца"""
    return role_required('owner')(view_func)


def manager_or_owner_required(view_func):
    """Декоратор для проверки прав менеджера или владельца"""
    return role_required(['manager', 'owner'])(view_func)


class CompanyPermissionMixin:
    """Миксин для проверки прав доступа к объектам компании"""
    
    def get_queryset(self):
        """Фильтруем объекты по текущей компании"""
        queryset = super().get_queryset()
        if hasattr(self.request, 'company'):
            return queryset.filter(company=self.request.company)
        return queryset.none()
    
    def dispatch(self, request, *args, **kwargs):
        """Проверяем доступ к компании"""
        if not hasattr(request, 'company') or not hasattr(request, 'company_user'):
            raise PermissionDenied("Доступ запрещен: не выбрана компания")
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin:
    """Миксин для проверки роли пользователя"""
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, 'company_user'):
            raise PermissionDenied("Доступ запрещен")
        
        if self.required_roles and request.company_user.role not in self.required_roles:
            raise PermissionDenied(
                f"Доступ запрещен: требуется роль {', '.join(self.required_roles)}"
            )
        return super().dispatch(request, *args, **kwargs)


class ExecutorPermissionMixin:
    """Миксин для исполнителей - доступ только к своим объектам"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, 'company_user'):
            if self.request.company_user.role == 'executor':
                # Исполнители видят только свои заказы
                return queryset.filter(executors__user=self.request.user)
        return queryset


# crm/context_processors.py
def company_context(request):
    """Контекстный процессор для добавления информации о компании"""
    context = {}
    
    if hasattr(request, 'company'):
        context['current_company'] = request.company
    
    if hasattr(request, 'company_user'):
        context['company_user'] = request.company_user
        context['user_role'] = request.company_user.role
        context['is_owner'] = request.company_user.role == 'owner'
        context['is_manager'] = request.company_user.role in ['manager', 'owner']
        context['is_executor'] = request.company_user.role == 'executor'
    
    return context


# crm/utils.py
from django.db.models import Q
from .models import Order, CompanyUser


def get_user_orders(user, company):
    """Получить заказы пользователя в зависимости от его роли"""
    try:
        company_user = CompanyUser.objects.get(user=user, company=company)
        
        if company_user.role in ['owner', 'manager']:
            # Владельцы и менеджеры видят все заказы компании
            return Order.objects.filter(company=company)
        elif company_user.role == 'executor':
            # Исполнители видят только назначенные им заказы
            return Order.objects.filter(
                company=company,
                executors__user=user
            ).distinct()
        else:
            return Order.objects.none()
    except CompanyUser.DoesNotExist:
        return Order.objects.none()


def can_user_access_order(user, order):
    """Проверить, может ли пользователь получить доступ к заказу"""
    try:
        company_user = CompanyUser.objects.get(
            user=user, 
            company=order.company,
            is_active=True
        )
        
        if company_user.role in ['owner', 'manager']:
            return True
        elif company_user.role == 'executor':
            return order.executors.filter(user=user).exists()
        
        return False
    except CompanyUser.DoesNotExist:
        return False


def calculate_user_commission(user, company, period_year, period_month):
    """Рассчитать комиссию пользователя за период"""
    try:
        company_user = CompanyUser.objects.get(user=user, company=company)
        
        # Получаем завершенные заказы пользователя за период
        completed_orders = Order.objects.filter(
            company=company,
            status='completed',
            completion_date__year=period_year,
            completion_date__month=period_month,
            executors__user=user
        ).distinct()
        
        total_commission = 0
        for order in completed_orders:
            # Рассчитываем комиссию как процент от суммы заказа
            commission = (order.total_amount * company_user.commission_rate) / 100
            total_commission += commission
        
        return total_commission
    except CompanyUser.DoesNotExist:
        return 0