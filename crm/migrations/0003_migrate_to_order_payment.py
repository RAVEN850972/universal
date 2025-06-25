# crm/migrations/0003_migrate_to_order_payment.py

from django.db import migrations
from decimal import Decimal


def migrate_to_order_payment(apps, schema_editor):
    """
    Миграция данных с комиссионной системы на оплату за заказы
    """
    OrderExecutor = apps.get_model('crm', 'OrderExecutor')
    CompanyUser = apps.get_model('crm', 'CompanyUser')
    
    # Обновляем существующие записи OrderExecutor
    for executor in OrderExecutor.objects.all():
        try:
            # Получаем данные пользователя в компании
            company_user = CompanyUser.objects.get(
                user=executor.user,
                company=executor.order.company
            )
            
            # Устанавливаем ставку за заказ
            if hasattr(company_user, 'order_rate') and company_user.order_rate > 0:
                # Если у исполнителя уже есть базовая ставка за заказ
                executor.order_rate = company_user.order_rate
                executor.payment_amount = company_user.order_rate
            else:
                # Если нет базовой ставки, рассчитываем из старых данных
                if hasattr(executor, 'commission_amount') and executor.commission_amount > 0:
                    # Используем старую комиссию как ставку за заказ
                    executor.order_rate = executor.commission_amount
                    executor.payment_amount = executor.commission_amount
                else:
                    # Устанавливаем базовую ставку в зависимости от суммы заказа
                    order_amount = float(executor.order.total_amount)
                    if order_amount >= 100000:
                        base_rate = Decimal('4000')  # Премиум заказы
                    elif order_amount >= 50000:
                        base_rate = Decimal('2500')  # Сложные заказы
                    elif order_amount >= 10000:
                        base_rate = Decimal('1500')  # Средние заказы
                    else:
                        base_rate = Decimal('1000')  # Простые заказы
                    
                    executor.order_rate = base_rate
                    executor.payment_amount = base_rate
                    
                    # Обновляем базовую ставку пользователя, если она не установлена
                    if company_user.order_rate == 0:
                        company_user.order_rate = base_rate
                        company_user.save()
            
            executor.save()
            
        except CompanyUser.DoesNotExist:
            # Если пользователь не найден в компании, устанавливаем стандартную ставку
            executor.order_rate = Decimal('1500')
            executor.payment_amount = Decimal('1500')
            executor.save()
        except Exception as e:
            # Логируем ошибку и продолжаем
            print(f"Ошибка при миграции OrderExecutor {executor.id}: {e}")
            continue


def reverse_migration(apps, schema_editor):
    """
    Обратная миграция (если потребуется откат)
    """
    # В случае отката сложно точно восстановить старые данные
    # Можно оставить как есть или реализовать примерное восстановление
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_change_to_order_rate'),
    ]

    operations = [
        migrations.RunPython(
            migrate_to_order_payment,
            reverse_migration,
        ),
    ]