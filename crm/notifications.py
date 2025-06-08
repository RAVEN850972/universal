from django.core.mail import send_mail
from django.template.loader import render_to_string

def send_order_notification(order, recipients):
    """Отправка уведомления о новом заказе"""
    subject = f'Новый заказ #{order.id}'
    html_message = render_to_string('emails/new_order.html', {
        'order': order,
        'company': order.company
    })
    
    send_mail(
        subject=subject,
        message='',  # Текстовая версия
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        html_message=html_message,
        fail_silently=False,
    )