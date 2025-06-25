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
                
                # Добавляем дополнительный контекст для шаблонов
                self._add_template_context(request)
                
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
    
    def _add_template_context(self, request):
        """Добавляем дополнительный контекст для использования в шаблонах"""
        try:
            # Количество новых заказов для бейджей
            if hasattr(request, 'company'):
                if request.company_user.role == 'executor':
                    # Для исполнителей - только их новые заказы
                    pending_orders = Order.objects.filter(
                        company=request.company,
                        executors__user=request.user,
                        status__in=['new', 'in_progress']
                    ).distinct().count()
                else:
                    # Для менеджеров и владельцев - все новые заказы
                    pending_orders = Order.objects.filter(
                        company=request.company,
                        status__in=['new', 'in_progress']
                    ).count()
                
                request.pending_orders_count = pending_orders
                
                # Количество компаний пользователя (для меню)
                request.user_companies_count = CompanyUser.objects.filter(
                    user=request.user,
                    is_active=True,
                    company__is_active=True
                ).count()
                
                # Количество уведомлений (пока заглушка)
                request.notifications_count = 0
                
        except Exception:
            # В случае ошибки просто игнорируем
            request.pending_orders_count = 0
            request.user_companies_count = 0
            request.notifications_count = 0