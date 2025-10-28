# email_utils/services.py
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def send_account_created_email(user, subject, template_name, context=None):
    if context is None:
        context = {}
    context['user'] = user  # always pass user

    # Use the template_name parameter
    message = render_to_string(template_name, context)

    email_msg = EmailMessage(
        subject=subject,
        body=message,
        from_email='your_email@gmail.com',  # or settings.DEFAULT_FROM_EMAIL
        to=[user.email]
    )
    email_msg.content_subtype = 'html'
    email_msg.send()
