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
    list_display = ('user', 'company', 'role', 'salary_rate', 'commission_rate', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at', 'company')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'company__name')
    readonly_fields = ('joined_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Админ для клиентов"""
    list_display = ('name', 'company', 'phone', 'email', 'source', 'orders_count', 'created_at')
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
    list_display = ('name', 'company', 'base_price', 'unit', 'is_active', 'orders_count')
    list_filter = ('is_active', 'company', 'created_at')
    search_fields = ('name', 'company__name')
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
    list_display = ('order', 'user', 'work_hours', 'commission_amount', 'status', 'assigned_at')
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


def calculate_commissions(modeladmin, request, queryset):
    """Массовый расчет комиссий"""
    from .utils import calculate_user_commission
    count = 0
    for salary_calc in queryset:
        commission = calculate_user_commission(
            salary_calc.user, 
            salary_calc.company, 
            salary_calc.period_year, 
            salary_calc.period_month
        )
        salary_calc.commission_total = commission
        salary_calc.save()
        count += 1
    
    modeladmin.message_user(request, f'Пересчитано комиссий: {count}')

calculate_commissions.short_description = "Пересчитать комиссии"

def pay_selected_salaries(modeladmin, request, queryset):
    from django.utils import timezone
    paid_count = 0

    for salary in queryset.filter(is_paid=False):
        salary.paid_amount += salary.total_amount
        salary.paid_at = timezone.now()
        salary.is_paid = (salary.paid_amount >= salary.total_amount)
        salary.save()
        FinancialTransaction.objects.create(
            company=salary.company,
            user=salary.user,
            transaction_type='salary',
            amount=salary.total_amount,
            description=f"Выплата зарплаты за {salary.period_month}/{salary.period_year}",
            transaction_date=timezone.now()
        )
        paid_count += 1

    modeladmin.message_user(request, f"Выплачено зарплат: {paid_count}")

pay_selected_salaries.short_description = "Выплатить выбранные зарплаты"

@admin.register(SalaryCalculation)
class SalaryCalculationAdmin(admin.ModelAdmin):
    """Админ для расчетов зарплаты"""
    list_display = ('user', 'company', 'period', 'total_amount', 'is_paid', 'calculated_at', 'paid_amount', 'remaining_amount')
    list_filter = ('is_paid', 'period_year', 'period_month', 'company')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('calculated_at', 'total_amount')

    actions = [calculate_commissions, pay_selected_salaries]
    
    def period(self, obj):
        return f"{obj.period_month:02d}/{obj.period_year}"
    period.short_description = 'Период'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company')

    def remaining_amount(self, obj):
        return obj.total_amount - obj.paid_amount
    remaining_amount.short_description = 'Остаток к выплате'

# Добавляем действия к соответствующим админкам
OrderAdmin.actions = [mark_orders_completed]