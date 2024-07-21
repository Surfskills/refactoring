# signals.py
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from .utils import send_email

@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    if created:
        token = RefreshToken.for_user(instance).access_token
        current_site = get_current_site(None).domain
        relativeLink = reverse('email-verify')
        absurl = f'http://{current_site}{relativeLink}?token={str(token)}'
        email_body = f'Hi {instance.username},\nUse the link below to verify your email:\n{absurl}'
        send_email('Verify your email', instance.email, email_body)
