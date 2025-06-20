from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
import json
from datetime import datetime

class Command(BaseCommand):
    help = 'Создает резервную копию данных'

    def handle(self, *args, **options):
        backup_data = {}
        
        # Модели для бэкапа
        models_to_backup = [
            'crm.Company',
            'crm.CompanyUser', 
            'crm.Client',
            'crm.Service',
            'crm.Order',
            'crm.OrderService',
            'crm.SalaryCalculation'
        ]
        
        for model_name in models_to_backup:
            app_label, model_class = model_name.split('.')
            model = apps.get_model(app_label, model_class)
            
            data = serializers.serialize('json', model.objects.all())
            backup_data[model_name] = json.loads(data)
        
        # Сохраняем в файл
        filename = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(f'Backup создан: {filename}')
        )