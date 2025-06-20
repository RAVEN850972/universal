import csv
from django.core.management.base import BaseCommand
from django.http import HttpResponse
from crm.models import Order, Client, FinancialTransaction


class Command(BaseCommand):
    help = 'Экспортирует данные в CSV файлы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['orders', 'clients', 'transactions'],
            required=True,
            help='Тип данных для экспорта'
        )
        parser.add_argument(
            '--company',
            type=int,
            help='ID компании для фильтрации'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='export.csv',
            help='Имя выходного файла'
        )

    def handle(self, *args, **options):
        data_type = options['type']
        company_id = options.get('company')
        output_file = options['output']

        self.stdout.write(f'Экспорт {data_type} в файл {output_file}')

        if data_type == 'orders':
            self.export_orders(output_file, company_id)
        elif data_type == 'clients':
            self.export_clients(output_file, company_id)
        elif data_type == 'transactions':
            self.export_transactions(output_file, company_id)

        self.stdout.write(self.style.SUCCESS(f'Экспорт завершен: {output_file}'))

    def export_orders(self, filename, company_id=None):
        queryset = Order.objects.select_related('client', 'company', 'created_by')
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'ID', 'Клиент', 'Компания', 'Статус', 'Сумма', 
                'Дата заказа', 'Дата завершения', 'Создал'
            ])
            
            for order in queryset:
                writer.writerow([
                    order.id,
                    order.client.name,
                    order.company.name,
                    order.get_status_display(),
                    order.total_amount,
                    order.order_date.strftime('%Y-%m-%d %H:%M'),
                    order.completion_date.strftime('%Y-%m-%d %H:%M') if order.completion_date else '',
                    order.created_by.get_full_name()
                ])

    def export_clients(self, filename, company_id=None):
        queryset = Client.objects.select_related('company')
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'ID', 'Имя', 'Компания', 'Телефон', 'Email', 
                'Источник', 'Дата создания'
            ])
            
            for client in queryset:
                writer.writerow([
                    client.id,
                    client.name,
                    client.company.name,
                    client.phone,
                    client.email,
                    client.get_source_display(),
                    client.created_at.strftime('%Y-%m-%d')
                ])

    def export_transactions(self, filename, company_id=None):
        queryset = FinancialTransaction.objects.select_related('company', 'user', 'order')
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'ID', 'Тип', 'Сумма', 'Компания', 'Пользователь', 
                'Заказ', 'Дата операции', 'Описание'
            ])
            
            for transaction in queryset:
                writer.writerow([
                    transaction.id,
                    transaction.get_transaction_type_display(),
                    transaction.amount,
                    transaction.company.name,
                    transaction.user.get_full_name() if transaction.user else '',
                    f'#{transaction.order.id}' if transaction.order else '',
                    transaction.transaction_date.strftime('%Y-%m-%d'),
                    transaction.description
                ])