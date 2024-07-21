from celery import shared_task
from django.utils import timezone
from .models import FileUpload
from django.core.mail import send_mail
import datetime

@shared_task
def send_file_expiration_email(file_id, user_email):
    file = FileUpload.objects.get(id=file_id)
    send_mail(
        'File Expiration Notice',
        f'Your file {file.file.name} will expire on {file.expires_at}.',
        'from@example.com',
        [user_email],
        fail_silently=False,
    )