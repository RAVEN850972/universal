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
