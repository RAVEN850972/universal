# crm/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Sum
from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ для расширенной модели пользователя"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('phone',)}),
    )


class CompanyUserInline(admin.TabularInline):
    """Inline для сотрудников компании"""
    model = CompanyUser
    extra = 0
    readonly_fields = ('joined_at',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Админ для компаний"""
    list_display = ('name', 'phone', 'email', 'employees_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CompanyUserInline]
    
    def employees_count(self, obj):
        return obj.company_users.filter(is_active=True).count()
    employees_count.short_description = 'Сотрудников'


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    """Админ для связи пользователь-компания"""
    # ИСПРАВЛЕНО: заменили commission_rate на order_rate
    list_display = ('user', 'company', 'role', 'salary_rate', 'order_rate', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at', 'company')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'company__name')
    readonly_fields = ('joined_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Админ для клиентов"""
    list_display = ('name', 'phone', 'email', 'company', 'source', 'created_at')
    list_filter = ('source', 'company', 'created_at')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    def orders_count(self, obj):
        return obj.orders.count()
    orders_count.short_description = 'Заказов'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Админ для услуг"""
    list_display = ('name', 'base_price', 'unit', 'company', 'is_active', 'created_at')
    list_filter = ('is_active', 'company', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def orders_count(self, obj):
        return obj.order_services.count()
    orders_count.short_description = 'В заказах'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


class OrderServiceInline(admin.TabularInline):
    """Inline для услуг в заказе"""
    model = OrderService
    extra = 0
    readonly_fields = ('total_price',)



class OrderExecutorInline(admin.TabularInline):
    """Inline для исполнителей заказа"""
    model = OrderExecutor
    extra = 0
    readonly_fields = ('assigned_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админ для заказов"""
    list_display = ('id', 'client', 'company', 'status', 'total_amount', 'order_date', 'created_by')
    list_filter = ('status', 'company', 'order_date', 'created_at')
    search_fields = ('id', 'client__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderServiceInline, OrderExecutorInline]
    date_hierarchy = 'order_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'company', 'created_by')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client":
            # Фильтруем клиентов по компании (если есть контекст)
            if hasattr(request, '_obj_'):
                kwargs["queryset"] = Client.objects.filter(company=request._obj_.company)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(OrderService)
class OrderServiceAdmin(admin.ModelAdmin):
    """Админ для услуг в заказах"""
    list_display = ('order', 'service', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__company', 'service')
    search_fields = ('order__id', 'service__name')
    readonly_fields = ('total_price',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'service')


@admin.register(OrderExecutor)
class OrderExecutorAdmin(admin.ModelAdmin):
    """Админ для исполнителей заказов"""
    # ИСПРАВЛЕНО: убрали work_hours и commission_amount, добавили order_rate и payment_amount
    list_display = ('order', 'user', 'order_rate', 'payment_amount', 'status', 'assigned_at')
    list_filter = ('status', 'assigned_at', 'order__company')
    search_fields = ('order__id', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('assigned_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'user')



    


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    """Админ для финансовых операций"""
    list_display = ('transaction_type', 'amount', 'company', 'user', 'order', 'transaction_date')
    list_filter = ('transaction_type', 'company', 'transaction_date')
    search_fields = ('description', 'user__username', 'order__id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'transaction_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'user', 'order')


@admin.register(SalaryCalculation)
class SalaryCalculationAdmin(admin.ModelAdmin):
    """Админ для расчетов зарплаты"""
    # ИСПРАВЛЕНО: убрали paid_amount, обновили поля согласно новой модели
    list_display = ('user', 'company', 'period_display', 'base_salary', 'orders_payment', 'completed_orders', 'total_amount', 'is_paid')
    list_filter = ('is_paid', 'company', 'period_year', 'period_month')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('calculated_at', 'total_amount')
    
    def period_display(self, obj):
        return f"{obj.period_month:02d}/{obj.period_year}"
    period_display.short_description = 'Период'
    
    def total_amount(self, obj):
        return f"{obj.total_amount:,.0f} ₽"
    total_amount.short_description = 'Итого'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company')

    def remaining_amount(self, obj):
        return obj.total_amount - obj.paid_amount
    remaining_amount.short_description = 'Остаток к выплате'

# Добавляем действия к соответствующим админкам
# Кастомизация админ-панели
admin.site.site_header = "Universal Service CRM"
admin.site.site_title = "CRM Admin"
admin.site.index_title = "Панель администрирования"


# Дополнительные действия для админки
def mark_orders_completed(modeladmin, request, queryset):
    """Массовое завершение заказов"""
    from django.utils import timezone
    updated = queryset.update(status='completed', completion_date=timezone.now())
    modeladmin.message_user(request, f'Завершено заказов: {updated}')

mark_orders_completed.short_description = "Отметить заказы как завершенные"


def calculate_orders_payment(modeladmin, request, queryset):
    """Массовый расчет оплаты за заказы"""
    from .utils import calculate_user_orders_payment
    count = 0
    for salary_calc in queryset:
        orders_data = calculate_user_orders_payment(
            salary_calc.user, 
            salary_calc.company, 
            salary_calc.period_year, 
            salary_calc.period_month
        )
        salary_calc.orders_payment = orders_data['total_payment']
        salary_calc.completed_orders = orders_data['orders_count']
        salary_calc.save()
        count += 1
    
    modeladmin.message_user(request, f'Пересчитано оплат за заказы: {count}')

calculate_orders_payment.short_description = "Пересчитать оплату за заказы"


def pay_selected_salaries(modeladmin, request, queryset):
    """Массовая выплата зарплат"""
    from django.utils import timezone
    count = 0
    for salary_calc in queryset.filter(is_paid=False):
        salary_calc.is_paid = True
        salary_calc.paid_at = timezone.now()
        salary_calc.save()
        
        # Создаем финансовую транзакцию
        FinancialTransaction.objects.create(
            company=salary_calc.company,
            user=salary_calc.user,
            transaction_type='salary',
            amount=salary_calc.total_amount,
            description=f"Выплата зарплаты за {salary_calc.period_month:02d}/{salary_calc.period_year}",
            transaction_date=timezone.now()
        )
        count += 1
    
    modeladmin.message_user(request, f'Выплачено зарплат: {count}')

pay_selected_salaries.short_description = "Отметить как выплаченные"


# Добавляем действия к соответствующим админкам
OrderAdmin.actions = [mark_orders_completed]
SalaryCalculationAdmin.actions = [calculate_orders_payment, pay_selected_salaries]