# crm/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import *


class ClientForm(forms.ModelForm):
    """Форма для создания/редактирования клиента"""
    
    class Meta:
        model = Client
        fields = ['name', 'address', 'phone', 'email', 'source', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя клиента'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Адрес клиента'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'source': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные заметки'
            }),
        }


class ServiceForm(forms.ModelForm):
    """Форма для создания/редактирования услуги"""
    
    class Meta:
        model = Service
        fields = ['name', 'description', 'base_price', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название услуги'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание услуги'
            }),
            'base_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'шт, час, м²'
            }),
        }


class OrderCreateForm(forms.ModelForm):
    """Форма для создания заказа"""
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            # Фильтруем клиентов по текущей компании
            self.fields['client'].queryset = self.company.clients.all()
            self.fields['client'].empty_label = "Выберите клиента"
    
    class Meta:
        model = Order
        fields = ['client', 'description', 'order_date']
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание заказа'
            }),
            'order_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
    
    def clean_order_date(self):
        order_date = self.cleaned_data['order_date']
        if order_date < timezone.now():
            raise ValidationError("Дата заказа не может быть в прошлом")
        return order_date
    
    def clean_order_total(self):
        """Дополнительная валидация суммы заказа"""
        total = self.cleaned_data.get('total_amount')
        if total and total < 0:
            raise ValidationError("Сумма заказа не может быть отрицательной")
        return total


class OrderServiceForm(forms.ModelForm):
    """Форма для добавления услуги к заказу"""
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['service'].queryset = self.company.services.filter(is_active=True)
    
    class Meta:
        model = OrderService
        fields = ['service', 'quantity', 'unit_price', 'notes']
        widgets = {
            'service': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }


class EmployeeForm(forms.Form):
    """Форма для добавления сотрудника"""
    
    # Если пользователь уже существует
    existing_user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="Выберите существующего пользователя",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Или создаем нового
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин нового пользователя'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Фамилия'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль для нового пользователя'
        }),
        required=False
    )
    
    # Данные для CompanyUser
    role = forms.ChoiceField(
        choices=CompanyUser.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    salary_rate = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    commission_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '100'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        existing_user = cleaned_data.get('existing_user')
        username = cleaned_data.get('username')
        
        if not existing_user and not username:
            raise ValidationError(
                "Выберите существующего пользователя или введите данные для создания нового"
            )
        
        if not existing_user and username:
            # Проверяем обязательные поля для нового пользователя
            required_fields = ['first_name', 'last_name', 'email', 'password']
            for field in required_fields:
                if not cleaned_data.get(field):
                    raise ValidationError(f"Поле {field} обязательно для нового пользователя")
        
        return cleaned_data


class CompanyForm(forms.ModelForm):
    """Форма для создания/редактирования компании"""
    
    class Meta:
        model = Company
        fields = ['name', 'description', 'address', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название компании'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание деятельности'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Адрес компании'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'info@company.com'
            }),
        }


class SalaryCalculationForm(forms.ModelForm):
    """Форма для расчета зарплаты"""
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            # Фильтруем пользователей по текущей компании
            self.fields['user'].queryset = User.objects.filter(
                company_memberships__company=self.company,
                company_memberships__is_active=True
            )
    
    class Meta:
        model = SalaryCalculation
        fields = ['user', 'period_year', 'period_month', 'base_salary', 'bonuses', 'penalties']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'period_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '2020',
                'max': '2030'
            }),
            'period_month': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '12'
            }),
            'base_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'bonuses': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'penalties': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }


class FinancialTransactionForm(forms.ModelForm):
    """Форма для добавления финансовой операции"""
    
    class Meta:
        model = FinancialTransaction
        fields = ['transaction_type', 'amount', 'description', 'transaction_date']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание операции'
            }),
            'transaction_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }


# Формы для поиска и фильтрации
class OrderFilterForm(forms.Form):
    """Форма для фильтрации заказов"""
    
    status = forms.ChoiceField(
        choices=[('', 'Все статусы')] + Order.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    client = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по клиенту'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class ClientFilterForm(forms.Form):
    """Форма для поиска клиентов"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по имени, телефону, email'
        })
    )
    source = forms.ChoiceField(
        choices=[('', 'Все источники')] + Client.SOURCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )