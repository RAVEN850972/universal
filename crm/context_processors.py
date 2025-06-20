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
    
    # Добавляем дополнительные счетчики
    if hasattr(request, 'pending_orders_count'):
        context['pending_orders_count'] = request.pending_orders_count
    
    if hasattr(request, 'user_companies_count'):
        context['user_companies_count'] = request.user_companies_count
    
    if hasattr(request, 'notifications_count'):
        context['notifications_count'] = request.notifications_count
    
    return context