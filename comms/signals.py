import logging
from django.db.models.signals import post_save
from authentication.models import User
from django.dispatch import receiver
from django.conf import settings
from .utils import send_email
from datetime import datetime

current_year = datetime.now().year

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        logger.info(f"New user created: {instance.username}")
        
        # Send welcome email to the new user
        subject = "Welcome to tooma!"
        message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #eaeaea;
                    border-radius: 5px;
                }}
                .header {{
                    background-color: #34D399;
                    color: #ffffff;
                    padding: 10px 0;
                    text-align: center;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    color: #6c757d;
                    padding: 10px 0;
                    text-align: center;
                    font-size: 12px;
                    border-top: 1px solid #eaeaea;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to tooma!</h1>
                </div>
                <p>Hi {instance.username},</p>
                <p>Welcome to tooma! We're thrilled to have you on board.</p>
                <p>Tooma is a versatile platform that empowers creators to effortlessly share their digital products with clients or a wider audience. You can choose to offer your products for free or monetize them by collecting payments through our platform.</p>
                <p>To get started, please visit our <a href="https://toomav2.vercel.app">website</a> and explore the various features we offer.</p>
                <p>If you have any questions or need assistance, feel free to contact us at <a href="mailto:support@tooma.app">support@tooma.app</a>.</p>
                <p>We look forward to helping you achieve your goals with our service.</p>
                <div class="footer">
                    <p>&copy; {current_year} tooma. All rights reserved.</p>
                    <p>tooma</p>
                </div>
            </div>
        </body>
        </html>
        """

        send_email(subject, instance.email, message)

        # Notify developer team
        subject = "New User Signed Up"
        message = f"<p>New user signed up: {instance.username}, {instance.email}</p>"
        send_email(subject, settings.DEVELOPER_EMAIL, message)
