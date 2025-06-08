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