from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from crm.models import Company, CompanyUser, SalaryCalculation
from crm.utils import calculate_user_commission


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

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        company_filter = options.get('company')

        self.stdout.write(f'Расчет зарплаты за {month:02d}/{year}')

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

                # Рассчитываем комиссию
                commission = calculate_user_commission(user, company, year, month)
                
                # Создаем расчет зарплаты
                salary_calc = SalaryCalculation.objects.create(
                    company=company,
                    user=user,
                    period_year=year,
                    period_month=month,
                    base_salary=company_user.salary_rate,
                    commission_total=commission,
                    bonuses=Decimal('0'),
                    penalties=Decimal('0')
                )
                
                total_calculated += 1
                total_amount += salary_calc.total_amount
                
                self.stdout.write(
                    f'  {user.get_full_name()}: {salary_calc.total_amount}₽ '
                    f'(оклад: {salary_calc.base_salary}₽, комиссия: {commission}₽)'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nРасчет завершен!\n'
                f'Обработано сотрудников: {total_calculated}\n'
                f'Общая сумма к выплате: {total_amount}₽'
            )
        )
