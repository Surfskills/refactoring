
from django.contrib.auth import authenticate
from authentication.models import User
import os
import random

from rest_framework.exceptions import AuthenticationFailed


def generate_username(name):

    username = "".join(name.split(' ')).lower()
    if not User.objects.filter(username=username).exists():
        return username
    else:
        random_username = username + str(random.randint(0, 1000))
        return generate_username(random_username)


def register_social_user(provider, user_id, email, name):
    filtered_user_by_email = User.objects.filter(email=email)

    if filtered_user_by_email.exists():
        registered_user = filtered_user_by_email.first()

        if provider == registered_user.auth_provider:
            return {
                'email': registered_user.email,
                'username': registered_user.username,
                'tokens': registered_user.tokens()
            }
        else:
            raise AuthenticationFailed(
                detail='Please continue your login using ' + registered_user.auth_provider)

    else:
        user = {
            'username': name, 'email': email,
            'password': os.environ.get('SOCIAL_SECRET')
        }
        user = User.objects.create_user(**user)
        user.is_active = True
        user.auth_provider = provider
        user.save()
        return {
            'email': user.email,
            'username': user.username,
            'tokens': user.tokens()
        }