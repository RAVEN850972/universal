# crm/migrations/0002_change_to_order_rate.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        # 1. Переименовываем commission_rate в order_rate для CompanyUser
        migrations.RenameField(
            model_name='companyuser',
            old_name='commission_rate',
            new_name='order_rate',
        ),
        
        # 2. Обновляем метаданные поля order_rate
        migrations.AlterField(
            model_name='companyuser',
            name='order_rate',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Фиксированная сумма за выполненный заказ',
                max_digits=10,
                verbose_name='Ставка за заказ'
            ),
        ),
        
        # 3. Удаляем work_hours из OrderExecutor
        migrations.RemoveField(
            model_name='orderexecutor',
            name='work_hours',
        ),
        
        # 4. Переименовываем commission_amount в payment_amount
        migrations.RenameField(
            model_name='orderexecutor',
            old_name='commission_amount',
            new_name='payment_amount',
        ),
        
        # 5. Добавляем order_rate в OrderExecutor
        migrations.AddField(
            model_name='orderexecutor',
            name='order_rate',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Сумма к выплате за выполнение данного заказа',
                max_digits=10,
                verbose_name='Ставка за заказ'
            ),
        ),
        
        # 6. Добавляем поле notes в OrderExecutor
        migrations.AddField(
            model_name='orderexecutor',
            name='notes',
            field=models.TextField(
                blank=True,
                help_text='Дополнительные заметки по выполнению заказа',
                verbose_name='Примечания'
            ),
        ),
        
        # 7. Обновляем метаданные payment_amount
        migrations.AlterField(
            model_name='orderexecutor',
            name='payment_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Итоговая сумма к оплате за заказ',
                max_digits=10,
                verbose_name='Сумма к оплате'
            ),
        ),
        
        # 8. Обновляем поля SalaryCalculation
        migrations.RenameField(
            model_name='salarycalculation',
            old_name='commission_total',
            new_name='orders_payment',
        ),
        
        migrations.AlterField(
            model_name='salarycalculation',
            name='orders_payment',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Общая сумма за выполненные заказы',
                max_digits=10,
                verbose_name='Оплата за заказы'
            ),
        ),
        
        # 9. Добавляем completed_orders в SalaryCalculation
        migrations.AddField(
            model_name='salarycalculation',
            name='completed_orders',
            field=models.IntegerField(
                default=0,
                help_text='Количество завершенных заказов за период',
                verbose_name='Выполнено заказов'
            ),
        ),
    ]