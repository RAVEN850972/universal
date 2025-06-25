# crm/management/commands/calculate_salaries.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from crm.models import Company, CompanyUser, SalaryCalculation
from crm.utils import calculate_user_orders_payment, calculate_bonus_for_orders_count


class Command(BaseCommand):
    help = 'Рассчитывает зарплату для всех сотрудников за указанный период'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Год для расчета (по умолчанию текущий)'
        )
        parser.add_argument(
            '--month',
            type=int,
            default=timezone.now().month,
            help='Месяц для расчета (по умолчанию текущий)'
        )
        parser.add_argument(
            '--company',
            type=str,
            help='ID или название компании для расчета (по умолчанию все компании)'
        )
        parser.add_argument(
            '--with-bonuses',
            action='store_true',
            help='Учитывать бонусы за количество заказов'
        )

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        company_filter = options.get('company')
        with_bonuses = options.get('with_bonuses', False)

        self.stdout.write(f'Расчет зарплаты за {month:02d}/{year}')
        if with_bonuses:
            self.stdout.write('С учетом бонусов за количество заказов')

        # Получаем компании для расчета
        companies = Company.objects.filter(is_active=True)
        if company_filter:
            if company_filter.isdigit():
                companies = companies.filter(id=int(company_filter))
            else:
                companies = companies.filter(name__icontains=company_filter)

        if not companies.exists():
            self.stdout.write(self.style.ERROR('Компании не найдены'))
            return

        total_calculated = 0
        total_amount = Decimal('0')

        for company in companies:
            self.stdout.write(f'\nОбработка компании: {company.name}')
            
            # Получаем всех активных сотрудников компании
            company_users = CompanyUser.objects.filter(
                company=company,
                is_active=True
            ).select_related('user')

            for company_user in company_users:
                user = company_user.user
                
                # Проверяем, есть ли уже расчет за этот период
                existing_calc = SalaryCalculation.objects.filter(
                    company=company,
                    user=user,
                    period_year=year,
                    period_month=month
                ).first()

                if existing_calc:
                    self.stdout.write(
                        f'  {user.get_full_name()}: уже рассчитано ({existing_calc.total_amount}₽)'
                    )
                    continue

                # Рассчитываем оплату за заказы
                orders_data = calculate_user_orders_payment(user, company, year, month)
                
                # Рассчитываем бонусы (если включено)
                bonuses = Decimal('0')
                if with_bonuses and orders_data['orders_count'] > 0:
                    bonus_amount = calculate_bonus_for_orders_count(
                        orders_data['orders_count'], 
                        company_user.order_rate
                    )
                    bonuses = Decimal(str(bonus_amount * orders_data['orders_count']))
                
                # Создаем расчет зарплаты
                salary_calc = SalaryCalculation.objects.create(
                    company=company,
                    user=user,
                    period_year=year,
                    period_month=month,
                    base_salary=company_user.salary_rate,
                    orders_payment=orders_data['total_payment'],
                    completed_orders=orders_data['orders_count'],
                    bonuses=bonuses,
                    penalties=Decimal('0')
                )
                
                total_calculated += 1
                total_amount += salary_calc.total_amount
                
                self.stdout.write(
                    f'  {user.get_full_name()}: {salary_calc.total_amount}₽ '
                    f'(оклад: {salary_calc.base_salary}₽, '
                    f'за заказы: {orders_data["total_payment"]}₽, '
                    f'заказов: {orders_data["orders_count"]}, '
                    f'ставка: {company_user.order_rate}₽/заказ'
                    f'{f", бонусы: {bonuses}₽" if bonuses > 0 else ""})'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nРасчет завершен!\n'
                f'Обработано сотрудников: {total_calculated}\n'
                f'Общая сумма к выплате: {total_amount}₽'
            )
        )