# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class User(AbstractUser):
    """Расширенная модель пользователя"""
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Company(models.Model):
    """Компания - основа мультитенантности"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"


class CompanyUser(models.Model):
    """Связь пользователя с компанией и его роль"""
    ROLE_CHOICES = [
        ('owner', 'Владелец'),
        ('manager', 'Менеджер'),
        ('executor', 'Исполнитель'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    salary_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # ИЗМЕНЕНО: Заменяем commission_rate на order_rate
    order_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Ставка за заказ',
        help_text='Фиксированная сумма за выполненный заказ'
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.get_role_display()})"

    class Meta:
        unique_together = ['company', 'user']
        verbose_name = "Сотрудник компании"
        verbose_name_plural = "Сотрудники компании"

    def get_total_orders(self):
        """Общее количество заказов исполнителя"""
        if self.role == 'executor':
            return self.user.executor_orders.count()
        return 0
    
    def get_completed_orders(self):
        """Количество завершенных заказов исполнителя"""
        if self.role == 'executor':
            return self.user.executor_orders.filter(order__status='completed').count()
        return 0
    
    def get_success_rate(self):
        """Процент успешно завершенных заказов"""
        total = self.get_total_orders()
        if total == 0:
            return 0
        completed = self.get_completed_orders()
        return round((completed / total) * 100, 1)
    
    def get_rating(self):
        """Рейтинг сотрудника (от 1 до 5)"""
        success_rate = self.get_success_rate()
        if success_rate >= 95:
            return 5
        elif success_rate >= 85:
            return 4
        elif success_rate >= 70:
            return 3
        elif success_rate >= 50:
            return 2
        else:
            return 1


class Client(models.Model):
    """Клиенты компании"""
    SOURCE_CHOICES = [
        ('website', 'Сайт'),
        ('referral', 'Рекомендация'),
        ('advertising', 'Реклама'),
        ('social_media', 'Соцсети'),
        ('other', 'Другое'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='other')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Service(models.Model):
    """Услуги компании"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, default='шт')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.base_price} руб/{self.unit}"

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


class Order(models.Model):
    """Заказы"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='orders')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    order_date = models.DateTimeField()
    completion_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Заказ #{self.id} - {self.client.name}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']


class OrderService(models.Model):
    """Услуги в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='order_services')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service.name} x{self.quantity}"

    class Meta:
        verbose_name = "Услуга в заказе"
        verbose_name_plural = "Услуги в заказах"


class OrderExecutor(models.Model):
    """Исполнители заказов"""
    STATUS_CHOICES = [
        ('assigned', 'Назначен'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершено'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='executors')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='executor_orders')
    
    # ИЗМЕНЕНО: Убираем work_hours, добавляем order_rate и payment_amount
    order_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Ставка за заказ',
        help_text='Сумма к выплате за выполнение данного заказа'
    )
    
    payment_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Сумма к оплате',
        help_text='Итоговая сумма к оплате за заказ'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
        help_text='Дополнительные заметки по выполнению заказа'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Автоматически устанавливаем сумму к оплате"""
        if not self.payment_amount and self.order_rate:
            self.payment_amount = self.order_rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - Заказ #{self.order.id}"

    class Meta:
        verbose_name = "Исполнитель заказа"
        verbose_name_plural = "Исполнители заказов"


class SalaryCalculation(models.Model):
    """Расчёт зарплаты"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='salary_calculations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_calculations')
    period_year = models.IntegerField()
    period_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # ИЗМЕНЕНО: Заменяем work_payment на orders_payment
    orders_payment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Оплата за заказы',
        help_text='Общая сумма за выполненные заказы'
    )
    
    completed_orders = models.IntegerField(
        default=0,
        verbose_name='Выполнено заказов',
        help_text='Количество завершенных заказов за период'
    )
    
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    penalties = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    calculated_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    @property
    def total_amount(self):
        """Итоговая сумма к выплате"""
        return self.base_salary + self.orders_payment + self.bonuses - self.penalties
    
    @property
    def average_per_order(self):
        """Средняя оплата за заказ"""
        if self.completed_orders > 0:
            return self.orders_payment / self.completed_orders
        return 0

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.period_month:02d}/{self.period_year}"

    class Meta:
        unique_together = ['company', 'user', 'period_year', 'period_month']
        verbose_name = "Расчёт зарплаты"
        verbose_name_plural = "Расчёты зарплат"
        ordering = ['-period_year', '-period_month']


class FinancialTransaction(models.Model):
    """Финансовые операции"""
    TRANSACTION_TYPES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
        ('salary', 'Зарплата'),
        ('commission', 'Комиссия'),
        ('bonus', 'Премия'),
        ('penalty', 'Штраф'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='transactions')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', blank=True, null=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} руб"

    class Meta:
        verbose_name = "Финансовая операция"
        verbose_name_plural = "Финансовые операции"
        ordering = ['-transaction_date']