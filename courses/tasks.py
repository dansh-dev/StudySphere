from celery import shared_task
from django.core.mail import send_mail

# This task sends emails to users, varying from Content notifications to enrollment notifications
@shared_task(bind=True)
def send_emails(self, subject ,content, recipient_list):
    message = content
    # Sends the email to the recipient list async
    send_mail(subject, message, 'studysphereauth@gmail.com', recipient_list)
