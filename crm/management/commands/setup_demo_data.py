from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta

from crm.models import *

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает демо-данные для тестирования CRM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед созданием новых',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очистка существующих данных...')
            FinancialTransaction.objects.all().delete()
            SalaryCalculation.objects.all().delete()
            OrderExecutor.objects.all().delete()
            OrderService.objects.all().delete()
            Order.objects.all().delete()
            Service.objects.all().delete()
            Client.objects.all().delete()
            CompanyUser.objects.all().delete()
            Company.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # Создаем суперпользователя если его нет
        if not User.objects.filter(is_superuser=True).exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Администратор',
                last_name='Системы'
            )
            self.stdout.write(f'Создан суперпользователь: admin/admin123')

        # Создаем компании
        companies_data = [
            {
                'name': 'Строительная компания "Мастер"',
                'description': 'Строительные и ремонтные работы',
                'address': 'г. Москва, ул. Строителей, 15',
                'phone': '+7 (495) 123-45-67',
                'email': 'info@master-build.ru'
            },
            {
                'name': 'Клининговые услуги "Чисто"',
                'description': 'Профессиональная уборка помещений',
                'address': 'г. Санкт-Петербург, пр. Невский, 50',
                'phone': '+7 (812) 987-65-43',
                'email': 'contact@clean-pro.ru'
            }
        ]

        companies = []
        for comp_data in companies_data:
            company = Company.objects.create(**comp_data)
            companies.append(company)
            self.stdout.write(f'Создана компания: {company.name}')

        # Создаем пользователей и привязываем к компаниям
        users_data = [
            {
                'username': 'owner1',
                'password': 'password123',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'email': 'owner@master-build.ru',
                'phone': '+7 (905) 123-45-67',
                'company_role': 'owner',
                'company_index': 0
            },
            {
                'username': 'manager1',
                'password': 'password123',
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'email': 'manager@master-build.ru',
                'phone': '+7 (905) 234-56-78',
                'company_role': 'manager',
                'company_index': 0,
                'salary_rate': 50000,
                'commission_rate': 5
            },
            {
                'username': 'executor1',
                'password': 'password123',
                'first_name': 'Алексей',
                'last_name': 'Строителев',
                'email': 'worker@master-build.ru',
                'phone': '+7 (905) 345-67-89',
                'company_role': 'executor',
                'company_index': 0,
                'salary_rate': 40000,
                'commission_rate': 10
            },
            {
                'username': 'owner2',
                'password': 'password123',
                'first_name': 'Елена',
                'last_name': 'Чистякова',
                'email': 'owner@clean-pro.ru',
                'phone': '+7 (905) 456-78-90',
                'company_role': 'owner',
                'company_index': 1
            }
        ]

        users = []
        for user_data in users_data:
            company_data = {
                'company_role': user_data.pop('company_role'),
                'company_index': user_data.pop('company_index'),
                'salary_rate': user_data.pop('salary_rate', 0),
                'commission_rate': user_data.pop('commission_rate', 0)
            }
            
            password = user_data.pop('password')
            user = User.objects.create_user(**user_data)
            user.set_password(password)
            user.save()
            
            # Привязываем к компании
            CompanyUser.objects.create(
                company=companies[company_data['company_index']],
                user=user,
                role=company_data['company_role'],
                salary_rate=company_data['salary_rate'],
                commission_rate=company_data['commission_rate']
            )
            
            users.append(user)
            self.stdout.write(f'Создан пользователь: {user.username}/{password}')

        # Создаем клиентов для первой компании
        clients_data = [
            {
                'name': 'ООО "Рога и Копыта"',
                'address': 'г. Москва, ул. Бизнес-центр, 10',
                'phone': '+7 (495) 111-22-33',
                'email': 'info@roga-kopyta.ru',
                'source': 'website'
            },
            {
                'name': 'Иванов Иван Иванович',
                'address': 'г. Москва, ул. Домашняя, 5, кв. 10',
                'phone': '+7 (905) 111-22-33',
                'email': 'ivan@gmail.com',
                'source': 'referral'
            },
            {
                'name': 'Кафе "Вкусно"',
                'address': 'г. Москва, ул. Гурманов, 25',
                'phone': '+7 (495) 333-44-55',
                'email': 'cafe@vkusno.ru',
                'source': 'advertising'
            }
        ]

        clients = []
        for client_data in clients_data:
            client = Client.objects.create(
                company=companies[0],
                **client_data
            )
            clients.append(client)

        # Создаем услуги для первой компании
        services_data = [
            {
                'name': 'Ремонт офиса под ключ',
                'description': 'Полный ремонт офисных помещений',
                'base_price': 2500,
                'unit': 'м²'
            },
            {
                'name': 'Укладка плитки',
                'description': 'Укладка керамической плитки',
                'base_price': 800,
                'unit': 'м²'
            },
            {
                'name': 'Малярные работы',
                'description': 'Покраска стен и потолков',
                'base_price': 300,
                'unit': 'м²'
            },
            {
                'name': 'Установка окон',
                'description': 'Монтаж пластиковых окон',
                'base_price': 5000,
                'unit': 'шт'
            }
        ]

        services = []
        for service_data in services_data:
            service = Service.objects.create(
                company=companies[0],
                **service_data
            )
            services.append(service)

        # Создаем заказы
        order_statuses = ['new', 'in_progress', 'completed']
        
        for i in range(10):
            order_date = timezone.now() - timedelta(days=random.randint(1, 30))
            status = random.choice(order_statuses)
            completion_date = None
            
            if status == 'completed':
                completion_date = order_date + timedelta(days=random.randint(1, 14))
            
            order = Order.objects.create(
                company=companies[0],
                client=random.choice(clients),
                created_by=users[1],  # manager1
                status=status,
                description=f'Заказ №{i+1} - тестовый заказ',
                order_date=order_date,
                completion_date=completion_date
            )
            
            # Добавляем услуги к заказу
            num_services = random.randint(1, 3)
            total_amount = 0
            
            for _ in range(num_services):
                service = random.choice(services)
                quantity = random.randint(1, 10)
                unit_price = service.base_price * (1 + random.uniform(-0.2, 0.3))
                
                order_service = OrderService.objects.create(
                    order=order,
                    service=service,
                    quantity=quantity,
                    unit_price=unit_price
                )
                total_amount += order_service.total_price
            
            order.total_amount = total_amount
            order.save()
            
            # Назначаем исполнителя
            OrderExecutor.objects.create(
                order=order,
                user=users[2],  # executor1
                work_hours=random.randint(4, 40),
                commission_amount=(total_amount * 10) / 100,
                status='completed' if status == 'completed' else 'assigned'
            )
            
            # Создаем финансовую транзакцию для завершенных заказов
            if status == 'completed':
                FinancialTransaction.objects.create(
                    company=companies[0],
                    order=order,
                    transaction_type='income',
                    amount=total_amount,
                    description=f'Оплата за заказ #{order.id}',
                    transaction_date=completion_date
                )

        # Создаем расчеты зарплаты
        current_date = timezone.now().date()
        for user in [users[1], users[2]]:  # manager1, executor1
            # За прошлый месяц
            last_month = current_date.replace(day=1) - timedelta(days=1)
            
            from crm.utils import calculate_user_commission
            commission = calculate_user_commission(
                user, companies[0], last_month.year, last_month.month
            )
            
            company_user = CompanyUser.objects.get(user=user, company=companies[0])
            
            SalaryCalculation.objects.create(
                company=companies[0],
                user=user,
                period_year=last_month.year,
                period_month=last_month.month,
                base_salary=company_user.salary_rate,
                commission_total=commission,
                bonuses=random.randint(0, 5000) if random.choice([True, False]) else 0,
                penalties=0,
                is_paid=True
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Демо-данные созданы успешно!\n'
                f'Компаний: {len(companies)}\n'
                f'Пользователей: {len(users)}\n'
                f'Клиентов: {len(clients)}\n'
                f'Услуг: {len(services)}\n'
                f'Заказов: 10\n\n'
                f'Учетные данные:\n'
                f'admin/admin123 (суперпользователь)\n'
                f'owner1/password123 (владелец)\n'
                f'manager1/password123 (менеджер)\n'
                f'executor1/password123 (исполнитель)'
            )
        )
