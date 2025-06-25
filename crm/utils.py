# crm/utils.py - Полностью обновленный файл для системы оплаты за заказы

from django.db.models import Sum, Count
from decimal import Decimal
from .models import Order, OrderExecutor, CompanyUser


def get_user_orders(user, company, role=None):
    """Получить заказы пользователя в зависимости от роли"""
    try:
        company_user = CompanyUser.objects.get(user=user, company=company)
        role = role or company_user.role
        
        if role in ['owner', 'manager']:
            # Владельцы и менеджеры видят все заказы компании
            return Order.objects.filter(company=company)
        elif role == 'executor':
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
    """Проверить может ли пользователь получить доступ к заказу"""
    try:
        company_user = CompanyUser.objects.get(user=user, company=order.company)
        
        if company_user.role in ['owner', 'manager']:
            return True
        elif company_user.role == 'executor':
            return order.executors.filter(user=user).exists()
        
        return False
    except CompanyUser.DoesNotExist:
        return False


# НОВЫЕ ФУНКЦИИ ДЛЯ СИСТЕМЫ ОПЛАТЫ ЗА ЗАКАЗЫ

def calculate_user_orders_payment(user, company, period_year, period_month):
    """Рассчитать оплату пользователя за выполненные заказы за период"""
    try:
        company_user = CompanyUser.objects.get(user=user, company=company)
        
        # Получаем все завершенные заказы пользователя за период
        completed_orders = OrderExecutor.objects.filter(
            order__company=company,
            user=user,
            status='completed',  # Только завершенные заказы
            completed_at__year=period_year,
            completed_at__month=period_month
        )
        
        total_payment = 0
        orders_count = completed_orders.count()
        
        for order_executor in completed_orders:
            # Суммируем оплату за каждый завершенный заказ
            total_payment += order_executor.payment_amount
        
        return {
            'total_payment': total_payment,
            'orders_count': orders_count,
            'average_per_order': total_payment / orders_count if orders_count > 0 else 0,
            'completed_orders': completed_orders
        }
        
    except CompanyUser.DoesNotExist:
        return {
            'total_payment': 0,
            'orders_count': 0,
            'average_per_order': 0,
            'completed_orders': []
        }


def get_executor_rate_for_order(user, company, order=None):
    """Получить базовую ставку исполнителя за заказ"""
    try:
        company_user = CompanyUser.objects.get(user=user, company=company)
        return company_user.order_rate
    except CompanyUser.DoesNotExist:
        return 0


def calculate_bonus_for_orders_count(orders_count, base_rate):
    """Рассчитать бонус в зависимости от количества выполненных заказов"""
    bonuses = {
        10: 0.1,   # 10+ заказов = +10% к каждому заказу
        20: 0.15,  # 20+ заказов = +15% к каждому заказу  
        30: 0.25,  # 30+ заказов = +25% к каждому заказу
    }
    
    bonus_multiplier = 0
    for threshold, multiplier in sorted(bonuses.items(), reverse=True):
        if orders_count >= threshold:
            bonus_multiplier = multiplier
            break
    
    return base_rate * bonus_multiplier


def suggest_order_rate(order, user=None):
    """Предложить ставку за заказ на основе сложности/суммы заказа"""
    base_rates = {
        'simple': 1000,    # Простые заказы до 10к
        'medium': 1500,    # Средние заказы 10к-50к  
        'complex': 2500,   # Сложные заказы 50к+
        'premium': 4000,   # Премиум заказы 100к+
    }
    
    order_amount = float(order.total_amount)
    
    if order_amount >= 100000:
        category = 'premium'
    elif order_amount >= 50000:
        category = 'complex'
    elif order_amount >= 10000:
        category = 'medium'
    else:
        category = 'simple'
    
    suggested_rate = base_rates[category]
    
    # Если указан пользователь, учитываем его базовую ставку
    if user:
        try:
            company_user = CompanyUser.objects.get(user=user, company=order.company)
            if company_user.order_rate > 0:
                # Берем максимум между предложенной и базовой ставкой пользователя
                suggested_rate = max(suggested_rate, company_user.order_rate)
        except CompanyUser.DoesNotExist:
            pass
    
    return suggested_rate


# ОБРАТНАЯ СОВМЕСТИМОСТЬ - оставляем старую функцию для существующего кода
def calculate_user_commission(user, company, period_year, period_month):
    """
    DEPRECATED: Используйте calculate_user_orders_payment
    Оставлено для обратной совместимости с существующим кодом
    """
    orders_data = calculate_user_orders_payment(user, company, period_year, period_month)
    return orders_data['total_payment']